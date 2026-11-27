"""Casos críticos de renovación y recuperación con BD, firma y correo reales."""

import hashlib
from datetime import datetime, timedelta

import jwt
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.models import (
    AuthSessionORM,
    PasswordResetTokenORM,
    RefreshTokenORM,
)
from app.repositories.token_repository import TokenRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.security.passwords import verify_password
from app.security.tokens import decodificar_access_token, decodificar_reset_token
from tests.security_support import TEST_JWT_SECRET, TEST_PASSWORD

pytestmark = pytest.mark.integration
NEW_PASSWORD = "NuevaClaveSegura123!"


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def me(client, tokens):
    return client.get(
        "/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )


def refresh(client, tokens):
    return client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})


def test_rotacion_conserva_familia_y_caducidad_maxima(
    api_client, db_session, crear_usuario, login
):
    """Rotar cambia ambos tokens y guarda solo el digest sin extender la sesión."""
    inicial = login(crear_usuario())
    anterior = db_session.scalar(
        select(RefreshTokenORM).where(
            RefreshTokenORM.token_hash == digest(inicial["refresh_token"])
        )
    )
    familia_id, caducidad = anterior.familia_id, anterior.expira_en

    respuesta = refresh(api_client, inicial)

    assert respuesta.status_code == 200, respuesta.text
    nuevos = respuesta.json()
    assert nuevos["access_token"] != inicial["access_token"]
    assert nuevos["refresh_token"] != inicial["refresh_token"]
    db_session.expire_all()
    guardado = db_session.scalar(
        select(RefreshTokenORM).where(
            RefreshTokenORM.token_hash == digest(nuevos["refresh_token"])
        )
    )
    assert anterior.revocado is True
    assert guardado.revocado is False
    assert guardado.familia_id == familia_id
    assert guardado.expira_en == caducidad
    assert guardado.token_hash != nuevos["refresh_token"]
    assert db_session.get(AuthSessionORM, familia_id).expira_en == caducidad
    assert decodificar_access_token(nuevos["access_token"])["sid"] == familia_id
    assert me(api_client, nuevos).status_code == 200


@pytest.mark.parametrize("caducado", ["refresh", "familia"])
def test_renovacion_rechaza_caducidad_persistida_sin_emitir_tokens(
    api_client, db_session, crear_usuario, login, caducado
):
    """La expiración almacenada se comprueba sin esperar a que pase el tiempo."""
    tokens = login(crear_usuario())
    registro = db_session.scalar(select(RefreshTokenORM))
    if caducado == "refresh":
        registro.expira_en = datetime(2000, 1, 1)
    else:
        db_session.get(AuthSessionORM, registro.familia_id).expira_en = datetime(
            2000, 1, 1
        )
    db_session.commit()

    respuesta = refresh(api_client, tokens)

    assert respuesta.status_code == 401
    assert "access_token" not in respuesta.json()
    assert db_session.scalar(select(func.count()).select_from(RefreshTokenORM)) == 1
    if caducado == "familia":
        assert me(api_client, tokens).status_code == 401


def test_logout_del_refresh_anterior_revoca_sus_descendientes(
    api_client, crear_usuario, login
):
    """Cerrar con un refresh ya rotado revoca la familia y conserva otra sesión."""
    usuario = crear_usuario()
    anterior = login(usuario)
    independiente = login(usuario)
    rotado = refresh(api_client, anterior)
    assert rotado.status_code == 200
    descendiente = rotado.json()

    respuesta = api_client.post(
        "/auth/logout", json={"refresh_token": anterior["refresh_token"]}
    )

    assert respuesta.status_code == 204
    assert me(api_client, anterior).status_code == 401
    assert me(api_client, descendiente).status_code == 401
    assert refresh(api_client, descendiente).status_code == 401
    assert me(api_client, independiente).status_code == 200
    assert refresh(api_client, independiente).status_code == 200


def test_access_firmado_con_version_distinta_rechaza_sesion_existente(
    api_client, crear_usuario, login
):
    """Exige la versión vigente aunque la firma y la familia sean válidas."""
    tokens = login(crear_usuario())
    assert me(api_client, tokens).status_code == 200
    claims = decodificar_access_token(tokens["access_token"])
    claims["ver"] += 1
    alterado = {"access_token": jwt.encode(claims, TEST_JWT_SECRET, algorithm="HS256")}

    assert me(api_client, alterado).status_code == 401
    assert me(api_client, tokens).status_code == 200


def test_restauracion_usa_el_sujeto_del_jwt_y_conserva_la_otra_cuenta(
    api_client, db_session, crear_usuario, login, solicitar_recuperacion
):
    """Un ID ajeno enviado por el cliente no cambia la cuenta objetivo del permiso."""
    primero = crear_usuario()
    segundo = crear_usuario(email="misty@example.com")
    sesiones_primero = [login(primero), login(primero)]
    sesion_segundo = login(segundo)
    permiso = solicitar_recuperacion(primero)
    assert decodificar_reset_token(permiso)["sub"] == str(primero.id)

    respuesta = api_client.post(
        "/auth/reset-password",
        json={
            "token": permiso,
            "password": NEW_PASSWORD,
            "usuario_id": str(segundo.id),
        },
    )

    assert respuesta.status_code == 200, respuesta.text
    repo = UsuarioRepository(db_session)
    actualizado = repo.obtener_por_id(primero.id)
    ajeno = repo.obtener_por_id(segundo.id)
    assert actualizado.token_version == primero.token_version + 1
    assert ajeno.token_version == segundo.token_version
    assert verify_password(NEW_PASSWORD, actualizado.password_hash)
    assert not verify_password(TEST_PASSWORD, actualizado.password_hash)
    assert verify_password(TEST_PASSWORD, ajeno.password_hash)
    assert not verify_password(NEW_PASSWORD, ajeno.password_hash)
    for sesion in sesiones_primero:
        assert me(api_client, sesion).status_code == 401
        assert refresh(api_client, sesion).status_code == 401
    assert me(api_client, sesion_segundo).status_code == 200
    assert refresh(api_client, sesion_segundo).status_code == 200
    assert (
        api_client.post(
            "/auth/login",
            json={
                "email": primero.email,
                "password": TEST_PASSWORD,
            },
        ).status_code
        == 401
    )
    nueva_sesion = login(primero, password=NEW_PASSWORD)
    assert me(api_client, nueva_sesion).status_code == 200
    assert (
        api_client.post(
            "/auth/reset-password",
            json={
                "token": permiso,
                "password": "OtraClaveSegura123!",
            },
        ).status_code
        == 401
    )
    assert me(api_client, nueva_sesion).status_code == 200


@pytest.mark.parametrize("caso", ["algoritmo", "jti", "version", "proposito"])
def test_solicitud_de_reset_invalida_no_cambia_clave_ni_consume_permiso_valido(
    api_client, db_session, crear_usuario, solicitar_recuperacion, caso
):
    """Un rechazo conserva la contraseña y permite usar después el enlace legítimo."""
    usuario = crear_usuario()
    valido = solicitar_recuperacion(usuario)
    claims = decodificar_reset_token(valido)
    algoritmo = "HS256"
    if caso == "algoritmo":
        algoritmo = "HS384"
    elif caso == "jti":
        claims["jti"] = "no-es-un-uuid"
    elif caso == "version":
        claims["ver"] = "0"
    else:
        claims["type"] = "access"
    invalido = jwt.encode(claims, TEST_JWT_SECRET, algorithm=algoritmo)

    respuesta = api_client.post(
        "/auth/reset-password",
        json={
            "token": invalido,
            "password": NEW_PASSWORD,
        },
    )

    assert respuesta.status_code == 401
    guardado = UsuarioRepository(db_session).obtener_por_id(usuario.id)
    assert guardado.password_hash == usuario.password_hash
    assert (
        TokenRepository(db_session)
        .obtener_password_reset_token_por_hash(digest(valido))
        .usado
        is False
    )
    assert (
        api_client.post(
            "/auth/reset-password",
            json={
                "token": valido,
                "password": NEW_PASSWORD,
            },
        ).status_code
        == 200
    )


def test_reset_rechaza_permiso_caducado_en_bd_aunque_el_jwt_siga_vigente(
    api_client, db_session, crear_usuario, solicitar_recuperacion
):
    """Verifica también la caducidad persistida del permiso, no solo exp del JWT."""
    usuario = crear_usuario()
    token = solicitar_recuperacion(usuario)
    registro = db_session.scalar(select(PasswordResetTokenORM))
    registro.expira_en = datetime(2000, 1, 1)
    db_session.commit()

    respuesta = api_client.post(
        "/auth/reset-password",
        json={
            "token": token,
            "password": NEW_PASSWORD,
        },
    )

    assert respuesta.status_code == 401
    assert (
        UsuarioRepository(db_session).obtener_por_id(usuario.id).password_hash
        == usuario.password_hash
    )
    db_session.expire_all()
    assert registro.usado is False


def test_limite_persistente_se_comparte_entre_sesiones_y_se_renueva_por_ventana(
    clean_database, db_session
):
    """Una sesión nueva no evita el límite; avanzar la ventana lo restablece."""
    ahora = datetime(2030, 1, 1)
    repo = TokenRepository(db_session)
    assert repo.limitar("prueba-limite", 2, 900, ahora) is True
    assert repo.limitar("prueba-limite", 2, 900, ahora) is True
    with Session(clean_database) as otra:
        assert TokenRepository(otra).limitar("prueba-limite", 2, 900, ahora) is False
    assert repo.limitar("prueba-limite", 2, 900, ahora + timedelta(seconds=900)) is True
