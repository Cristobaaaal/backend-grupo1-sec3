"""JWT de recuperación reales: propósito, versión, caducidad e identificadores."""

from uuid import UUID

import jwt
import pytest
from pydantic import ValidationError

from app.schemas.auth_schemas import RestablecerRequest
from app.security.tokens import (
    crear_access_token,
    crear_reset_token,
    decodificar_access_token,
    decodificar_reset_token,
)
from tests.security_support import TEST_JWT_SECRET, access_payload

pytestmark = pytest.mark.unit


def test_reset_jwt_incluye_proposito_version_y_caducidad_breve():
    """Emite un permiso específico sin claims de sesión ni datos sensibles."""
    contenido = decodificar_reset_token(crear_reset_token(UUID(int=1), 3))

    assert contenido["sub"] == str(UUID(int=1))
    assert contenido["type"] == "password_reset"
    assert contenido["ver"] == 3
    assert contenido["exp"] - contenido["iat"] == 900
    assert UUID(contenido["jti"]).version == 4
    assert set(contenido) == {"sub", "iat", "exp", "jti", "type", "ver"}


def test_access_y_reset_no_son_intercambiables():
    """Los dos validadores rechazan un JWT legítimo emitido para el otro uso."""
    access = crear_access_token(UUID(int=1), str(UUID(int=8)), 0)
    recuperacion = crear_reset_token(UUID(int=1), 0)

    with pytest.raises(jwt.InvalidTokenError):
        decodificar_reset_token(access)
    with pytest.raises(jwt.InvalidTokenError):
        decodificar_access_token(recuperacion)


@pytest.mark.parametrize("claim", ["sub", "iat", "exp", "jti", "type", "ver"])
def test_reset_rechaza_claim_obligatorio_ausente(claim):
    """La firma correcta no compensa un claim obligatorio ausente."""
    contenido = access_payload(type="password_reset")
    contenido.pop("sid")
    contenido.pop(claim)
    token = jwt.encode(contenido, TEST_JWT_SECRET, algorithm="HS256")

    with pytest.raises(jwt.MissingRequiredClaimError):
        decodificar_reset_token(token)


@pytest.mark.parametrize(
    ("claim", "valor"),
    [
        ("ver", True),
        ("ver", "0"),
        ("ver", 0.5),
        ("jti", "invalido"),
        ("sub", "invalido"),
    ],
    ids=[
        "version-booleana",
        "version-texto",
        "version-decimal",
        "jti-invalido",
        "sub-invalido",
    ],
)
def test_reset_rechaza_version_o_identificador_invalido(claim, valor):
    """Exige una versión entera y UUID válidos para sujeto e identificador."""
    contenido = access_payload(type="password_reset", **{claim: valor})
    contenido.pop("sid")
    token = jwt.encode(contenido, TEST_JWT_SECRET, algorithm="HS256")

    with pytest.raises(jwt.InvalidTokenError):
        decodificar_reset_token(token)


@pytest.mark.parametrize(
    "longitud", [0, 11, 129], ids=["vacia", "menor-a-doce", "mas-de-128"]
)
def test_reset_aplica_la_politica_de_password(longitud):
    """Restablecer exige el mismo rango de 12 a 128 caracteres que registrar."""
    with pytest.raises(ValidationError) as error:
        RestablecerRequest(token="token-de-prueba", password="a" * longitud)

    assert error.value.errors()[0]["loc"] == ("password",)


@pytest.mark.parametrize("longitud", [12, 128], ids=["minimo-valido", "maximo-valido"])
def test_reset_acepta_los_limites_validos_de_password(longitud):
    """Admite exactamente ambos límites de la política de contraseña."""
    datos = RestablecerRequest(token="token-de-prueba", password="a" * longitud)

    assert len(datos.password) == longitud
