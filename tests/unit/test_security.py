"""Argon2, validación JWT y permisos reales, aislados de BD y HTTP."""

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

import jwt
import pytest
from fastapi import HTTPException

from app.domain.models import RolUsuario, Usuario
from app.security.passwords import hash_password, verify_password
from app.security.permissions import require_roles
from app.security.tokens import crear_access_token, decodificar_access_token
from tests.security_support import (
    TEST_JWT_SECRET,
    TEST_PASSWORD,
    access_payload,
    alterar_firma,
)

pytestmark = pytest.mark.unit


def test_argon2_protege_la_clave_y_rechaza_otra_password():
    """Un hash Argon2id valida la clave correcta y rechaza otra."""
    password_hash = hash_password(TEST_PASSWORD)

    assert password_hash.startswith("$argon2id$")
    assert password_hash != TEST_PASSWORD
    assert verify_password(TEST_PASSWORD, password_hash) is True
    assert verify_password("OtraClaveIncorrecta123!", password_hash) is False


def test_argon2_usa_sales_distintas_para_la_misma_password():
    """Dos altas con la misma clave no almacenan un hash idéntico."""
    primero = hash_password(TEST_PASSWORD)
    segundo = hash_password(TEST_PASSWORD)

    assert primero != segundo
    assert verify_password(TEST_PASSWORD, primero)
    assert verify_password(TEST_PASSWORD, segundo)


@pytest.mark.parametrize(
    "password_hash",
    ["no-es-un-hash", "$argon2id$incompleto"],
    ids=["formato-invalido", "argon2-incompleto"],
)
def test_hash_invalido_se_rechaza_sin_romper_la_autenticacion(password_hash):
    """Un hash corrupto se trata como credencial inválida."""
    assert verify_password(TEST_PASSWORD, password_hash) is False


def test_jwt_valido_contiene_identidad_caducidad_y_proposito():
    """Verifica claims firmados y la duración de 15 minutos del entorno de test."""
    usuario_id = UUID(int=5)

    contenido = decodificar_access_token(crear_access_token(usuario_id))

    assert contenido["sub"] == str(usuario_id)
    assert contenido["type"] == "access"
    assert contenido["exp"] - contenido["iat"] == 15 * 60
    assert UUID(contenido["jti"]).version == 4
    assert set(contenido) == {"sub", "iat", "exp", "jti", "type"}


def test_dos_access_tokens_tienen_identificadores_distintos():
    """Dos emisiones para la misma cuenta tienen jti distintos."""
    usuario_id = UUID(int=5)
    primero = decodificar_access_token(crear_access_token(usuario_id))
    segundo = decodificar_access_token(crear_access_token(usuario_id))

    assert primero["jti"] != segundo["jti"]


def test_jwt_manipulado_se_rechaza_por_la_firma():
    """Alterar la firma de un token real impide validarlo."""
    token = crear_access_token(UUID(int=5))

    with pytest.raises(jwt.InvalidSignatureError):
        decodificar_access_token(alterar_firma(token))


def test_jwt_vencido_se_rechaza_sin_esperas():
    """Un token firmado con exp en el pasado es rechazado inmediatamente."""
    pasado = datetime(2000, 1, 1, tzinfo=UTC)
    token = jwt.encode(
        access_payload(iat=pasado, exp=pasado), TEST_JWT_SECRET, algorithm="HS256"
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decodificar_access_token(token)


def test_jwt_de_recuperacion_no_se_acepta_como_access():
    """Una firma válida no permite intercambiar propósitos."""
    token = jwt.encode(
        access_payload(type="password_reset"), TEST_JWT_SECRET, algorithm="HS256"
    )

    with pytest.raises(jwt.InvalidTokenError, match="Tipo de token"):
        decodificar_access_token(token)


@pytest.mark.parametrize("algoritmo", ["HS384", "none"], ids=["otro-hmac", "sin-firma"])
def test_jwt_rechaza_algoritmos_fuera_de_la_configuracion(algoritmo):
    """No confía en el algoritmo declarado por la cabecera del atacante."""
    clave = "" if algoritmo == "none" else TEST_JWT_SECRET
    token = jwt.encode(access_payload(), clave, algorithm=algoritmo)

    with pytest.raises(jwt.InvalidAlgorithmError):
        decodificar_access_token(token)


@pytest.mark.parametrize("claim", ["sub", "iat", "exp", "jti", "type"])
def test_jwt_rechaza_claims_obligatorios_ausentes(claim):
    """La validación exige cada claim aunque la firma sea correcta."""
    datos = access_payload()
    del datos[claim]
    token = jwt.encode(datos, TEST_JWT_SECRET, algorithm="HS256")

    with pytest.raises(jwt.MissingRequiredClaimError):
        decodificar_access_token(token)


@pytest.mark.parametrize(
    "sujeto", ["no-es-un-uuid", 123, None], ids=["uuid-invalido", "numero", "nulo"]
)
def test_jwt_rechaza_sujeto_invalido(sujeto):
    """No permite identificar una cuenta con un sub inválido."""
    token = jwt.encode(access_payload(sub=sujeto), TEST_JWT_SECRET, algorithm="HS256")

    with pytest.raises(jwt.InvalidTokenError):
        decodificar_access_token(token)


@pytest.mark.parametrize("clave", [None, "corta"], ids=["ausente", "demasiado-corta"])
def test_emision_rechaza_secreto_ausente_o_corto(monkeypatch, clave):
    """Impide emitir tokens con una configuración de clave inválida."""
    if clave is None:
        monkeypatch.delenv("JWT_SECRET", raising=False)
    else:
        monkeypatch.setenv("JWT_SECRET", clave)

    with pytest.raises(RuntimeError, match="32 bytes"):
        crear_access_token(UUID(int=5))


@pytest.mark.parametrize(
    ("variable", "valor", "mensaje"),
    [
        ("JWT_ALGORITHM", "RS256", "JWT_ALGORITHM"),
        ("ACCESS_TOKEN_EXPIRE_MINUTES", "0", "positivo"),
    ],
    ids=["algoritmo-no-soportado", "duracion-cero"],
)
def test_emision_rechaza_configuracion_invalida(monkeypatch, variable, valor, mensaje):
    """Evita emitir un token cuando la configuración de seguridad es inválida."""
    monkeypatch.setenv(variable, valor)

    with pytest.raises(RuntimeError, match=mensaje):
        crear_access_token(UUID(int=5))


@pytest.mark.parametrize(
    "rol",
    [RolUsuario.ADMIN, RolUsuario.VETERINARIO, RolUsuario.ENTRENADOR],
)
def test_permiso_de_gestion_de_centros_depende_del_rol(rol):
    """ADMIN y VETERINARIO pueden gestionar centros; ENTRENADOR recibe 403."""
    usuario = Usuario(UUID(int=1), "rol@example.com", "hash-de-prueba", "Usuario", rol)
    comprobar = require_roles(RolUsuario.ADMIN, RolUsuario.VETERINARIO)

    if rol == RolUsuario.ENTRENADOR:
        with pytest.raises(HTTPException) as error:
            comprobar(usuario)
        assert error.value.status_code == 403
    else:
        assert comprobar(usuario) == usuario


def test_rol_administrador_no_se_hereda_de_un_veterinario():
    """El permiso de eliminación exclusivo de ADMIN rechaza VETERINARIO."""
    admin = Usuario(
        UUID(int=1), "rol@example.com", "hash-de-prueba", "Usuario", RolUsuario.ADMIN
    )
    comprobar = require_roles(RolUsuario.ADMIN)

    assert comprobar(admin) == admin
    with pytest.raises(HTTPException) as error:
        comprobar(replace(admin, rol=RolUsuario.VETERINARIO))
    assert error.value.status_code == 403
