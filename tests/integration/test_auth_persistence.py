"""Restricciones y estados persistidos; no sustituyen los flujos JWT de recuperación."""

import hashlib
from dataclasses import replace
from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.models import PasswordResetToken, RefreshToken
from app.repositories.token_repository import TokenRepository
from app.repositories.usuario_repository import UsuarioRepository

pytestmark = pytest.mark.integration


def test_bd_impone_email_unico_incluso_sin_el_servicio(db_session, crear_usuario):
    """El índice único impide duplicados al acceder directamente al repositorio."""
    original = crear_usuario()

    with pytest.raises(IntegrityError):
        UsuarioRepository(db_session).crear(
            replace(original, id=uuid4(), email="ASH@example.com")
        )
    # El servicio maneja este error con rollback; aquí se comprueba el índice real.
    db_session.rollback()

    assert (
        UsuarioRepository(db_session).obtener_por_email("ash@example.com") == original
    )


def test_revocacion_global_no_afecta_sesiones_de_otro_usuario(
    db_session, crear_usuario, login
):
    """Revoca todos los refresh del sujeto solicitado y conserva los ajenos."""
    primero = crear_usuario()
    segundo = crear_usuario(email="misty@example.com")
    sesiones = [login(primero), login(primero), login(segundo)]
    repositorio = TokenRepository(db_session)

    repositorio.revocar_todos_los_refresh_tokens_del_usuario(primero.id)

    estados = [
        repositorio.obtener_refresh_token_por_hash(
            hashlib.sha256(sesion["refresh_token"].encode()).hexdigest()
        ).revocado
        for sesion in sesiones
    ]
    assert estados == [True, True, False]


def test_consumo_de_permiso_de_recuperacion_persiste_en_otra_sesion(
    clean_database, db_session, crear_usuario
):
    """La marca usado queda persistida junto a sujeto y caducidad del permiso."""
    usuario = crear_usuario()
    token = PasswordResetToken(
        id=uuid4(),
        token_hash=hashlib.sha256(b"permiso-de-prueba").hexdigest(),
        usuario_id=usuario.id,
        expira_en=datetime(2030, 1, 1),
        creado_en=datetime(2026, 1, 1),
    )
    repositorio = TokenRepository(db_session)
    guardado = repositorio.guardar_password_reset_token(token)
    assert guardado.usado is False

    repositorio.marcar_password_reset_token_usado(token.id)

    with Session(clean_database) as nueva_sesion:
        persistido = TokenRepository(
            nueva_sesion
        ).obtener_password_reset_token_por_hash(token.token_hash)
        assert persistido.usado is True
        assert persistido.usuario_id == usuario.id
        assert persistido.expira_en == token.expira_en
        assert persistido.id == token.id


def test_invalidar_recuperacion_pendiente_solo_afecta_al_usuario_objetivo(
    db_session, crear_usuario
):
    """Invalida los permisos pendientes de una cuenta sin consumir los de otra."""
    primero = crear_usuario()
    segundo = crear_usuario(email="misty@example.com")
    repositorio = TokenRepository(db_session)
    tokens = []
    for indice, usuario in enumerate([primero, primero, segundo]):
        tokens.append(
            repositorio.guardar_password_reset_token(
                PasswordResetToken(
                    id=uuid4(),
                    token_hash=hashlib.sha256(f"permiso-{indice}".encode()).hexdigest(),
                    usuario_id=usuario.id,
                    expira_en=datetime(2030, 1, 1),
                    creado_en=datetime(2026, 1, 1),
                )
            )
        )

    repositorio.invalidar_tokens_recuperacion_pendientes(primero.id)

    assert [
        repositorio.obtener_password_reset_token_por_hash(token.token_hash).usado
        for token in tokens
    ] == [True, True, False]


@pytest.fixture(params=["refresh", "recuperacion"])
def tipo_de_token(request, db_session):
    """Permite comprobar las mismas restricciones en las dos tablas reales."""
    repositorio = TokenRepository(db_session)
    if request.param == "refresh":
        return (
            RefreshToken,
            repositorio.guardar_refresh_token,
            repositorio.obtener_refresh_token_por_hash,
        )
    return (
        PasswordResetToken,
        repositorio.guardar_password_reset_token,
        repositorio.obtener_password_reset_token_por_hash,
    )


def test_hash_de_token_duplicado_es_rechazado_por_la_bd(
    db_session, crear_usuario, tipo_de_token
):
    """El índice único impide que dos registros representen el mismo token."""
    modelo, guardar, obtener = tipo_de_token
    usuario = crear_usuario()
    original = modelo(
        id=uuid4(),
        token_hash=hashlib.sha256(b"token-unico").hexdigest(),
        usuario_id=usuario.id,
        expira_en=datetime(2030, 1, 1),
        creado_en=datetime(2026, 1, 1),
    )
    guardar(original)

    with pytest.raises(IntegrityError):
        guardar(replace(original, id=uuid4()))
    db_session.rollback()

    assert obtener(original.token_hash).id == original.id


def test_token_no_puede_persistirse_sin_usuario_real(db_session, tipo_de_token):
    """La clave foránea impide guardar permisos o sesiones sin su cuenta."""
    modelo, guardar, obtener = tipo_de_token
    token = modelo(
        id=uuid4(),
        token_hash=hashlib.sha256(b"token-huerfano").hexdigest(),
        usuario_id=uuid4(),
        expira_en=datetime(2030, 1, 1),
        creado_en=datetime(2026, 1, 1),
    )

    with pytest.raises(IntegrityError):
        guardar(token)
    db_session.rollback()

    assert obtener(token.token_hash) is None
