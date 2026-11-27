"""Decisiones de autenticación con repositorios dobles y reloj controlado."""

import hashlib
import smtplib
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, create_autospec
from uuid import UUID

import pytest

from app.core.exceptions import AuthenticationError, ConflictError
from app.domain.models import RefreshToken, RolUsuario, Usuario
from app.repositories.token_repository import TokenRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.auth_schemas import LoginRequest, RegistroRequest
from app.services import auth_service
from app.services.auth_service import AuthService
from tests.security_support import TEST_PASSWORD

pytestmark = pytest.mark.unit


@pytest.fixture
def caso_auth(monkeypatch):
    """Aísla repositorios, hashing y firma; las primitivas tienen pruebas reales."""
    usuarios = create_autospec(UsuarioRepository, instance=True, spec_set=True)
    tokens = create_autospec(TokenRepository, instance=True, spec_set=True)
    usuario = Usuario(
        UUID(int=1),
        "ash@example.com",
        "hash-simulado",
        "Ash",
        RolUsuario.ENTRENADOR,
        intentos_fallidos=4,
    )
    usuarios.obtener_por_email.return_value = usuario
    tokens.obtener_refresh_token_por_hash.return_value = None
    tokens.guardar_sesion.return_value = True
    ahora = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
    reloj = Mock(wraps=datetime)
    reloj.now.return_value = ahora
    generar_hash = Mock(return_value="hash-simulado")
    verificar = Mock(return_value=True)
    emitir = Mock(return_value="access-simulado")
    monkeypatch.setattr(auth_service, "datetime", reloj)
    monkeypatch.setattr(auth_service, "hash_password", generar_hash)
    monkeypatch.setattr(auth_service, "verify_password", verificar)
    monkeypatch.setattr(auth_service, "crear_access_token", emitir)
    return SimpleNamespace(
        usuarios=usuarios,
        tokens=tokens,
        usuario=usuario,
        ahora=ahora,
        hash=generar_hash,
        verificar=verificar,
        emitir=emitir,
        servicio=AuthService(usuarios, tokens),
        credenciales=LoginRequest(email=usuario.email, password=TEST_PASSWORD),
    )


def test_registro_asigna_rol_basico_y_guarda_hash(caso_auth):
    """El servicio normaliza el correo y prepara un usuario sin privilegios extra."""
    caso_auth.usuarios.obtener_por_email.return_value = None
    caso_auth.usuarios.crear.side_effect = lambda usuario: usuario
    datos = RegistroRequest(
        email="ASH@example.com", nombre_completo="Ash", password=TEST_PASSWORD
    )

    usuario = caso_auth.servicio.registrar(datos)

    assert usuario.email == "ash@example.com"
    assert usuario.rol == RolUsuario.ENTRENADOR
    assert usuario.password_hash == "hash-simulado"
    caso_auth.hash.assert_called_once_with(TEST_PASSWORD)
    caso_auth.usuarios.crear.assert_called_once_with(usuario)


def test_registro_duplicado_se_rechaza_antes_de_guardar(caso_auth):
    """No crea una segunda cuenta cuando el correo ya está registrado."""
    datos = RegistroRequest(
        email="ash@example.com", nombre_completo="Ash", password=TEST_PASSWORD
    )

    with pytest.raises(ConflictError):
        caso_auth.servicio.registrar(datos)

    caso_auth.usuarios.crear.assert_not_called()
    caso_auth.hash.assert_not_called()


def test_login_correcto_limpia_intentos_y_persiste_solo_hash_del_refresh(caso_auth):
    """Una autenticación válida limpia el contador y prepara una sesión de siete días."""
    resultado = caso_auth.servicio.login(caso_auth.credenciales)

    caso_auth.usuarios.actualizar_intentos_fallidos.assert_called_once_with(
        caso_auth.usuario.id, 0, None
    )
    registro, version = caso_auth.tokens.guardar_sesion.call_args.args
    caso_auth.emitir.assert_called_once_with(
        caso_auth.usuario.id, registro.familia_id, caso_auth.usuario.token_version
    )
    assert UUID(registro.familia_id).version == 4
    assert version == caso_auth.usuario.token_version
    assert registro.usuario_id == caso_auth.usuario.id
    assert (
        registro.token_hash
        == hashlib.sha256(resultado.refresh_token.encode()).hexdigest()
    )
    assert registro.token_hash != resultado.refresh_token
    assert registro.expira_en - registro.creado_en == timedelta(days=7)
    assert registro.revocado is False
    assert resultado.access_token == "access-simulado"


def test_quinto_intento_incorrecto_bloquea_sin_emitir_tokens(caso_auth):
    """El quinto fallo registra un bloqueo de quince minutos y devuelve error genérico."""
    caso_auth.verificar.return_value = False

    with pytest.raises(AuthenticationError) as error:
        caso_auth.servicio.login(caso_auth.credenciales)

    assert error.value.http_status == 401
    caso_auth.usuarios.actualizar_intentos_fallidos.assert_called_once_with(
        caso_auth.usuario.id,
        5,
        (caso_auth.ahora + timedelta(minutes=15)).replace(tzinfo=None),
    )
    caso_auth.emitir.assert_not_called()
    caso_auth.tokens.guardar_sesion.assert_not_called()


def test_usuario_inexistente_no_genera_una_sesion(caso_auth):
    """Un correo desconocido produce el mismo tipo de error y no crea tokens."""
    caso_auth.usuarios.obtener_por_email.return_value = None

    with pytest.raises(AuthenticationError) as error:
        caso_auth.servicio.login(caso_auth.credenciales)

    assert error.value.code == "AUTHENTICATION_ERROR"
    caso_auth.usuarios.actualizar_intentos_fallidos.assert_not_called()
    caso_auth.emitir.assert_not_called()
    caso_auth.tokens.guardar_sesion.assert_not_called()


@pytest.mark.parametrize("estado", ["inactivo", "bloqueado"])
def test_cuenta_no_disponible_rechaza_login_antes_de_verificar_password(
    caso_auth, estado
):
    """Las cuentas inactivas o con bloqueo vigente no obtienen una sesión."""
    if estado == "inactivo":
        caso_auth.usuario.activo = False
    else:
        caso_auth.usuario.bloqueado_hasta = caso_auth.ahora + timedelta(minutes=1)

    with pytest.raises(AuthenticationError):
        caso_auth.servicio.login(caso_auth.credenciales)

    caso_auth.verificar.assert_not_called()
    caso_auth.emitir.assert_not_called()
    caso_auth.tokens.guardar_sesion.assert_not_called()


def test_primer_fallo_tras_caducar_bloqueo_reinicia_el_contador(caso_auth):
    """Una fecha de bloqueo pasada permite un ciclo nuevo sin esperar en tiempo real."""
    caso_auth.usuario.intentos_fallidos = 5
    caso_auth.usuario.bloqueado_hasta = caso_auth.ahora - timedelta(seconds=1)
    caso_auth.verificar.return_value = False

    with pytest.raises(AuthenticationError):
        caso_auth.servicio.login(caso_auth.credenciales)

    caso_auth.usuarios.actualizar_intentos_fallidos.assert_called_once_with(
        caso_auth.usuario.id, 1, None
    )


def test_login_rechaza_si_la_version_cambio_antes_de_guardar_sesion(caso_auth):
    """El servicio no entrega una sesión si el guardado atómico la rechaza."""
    caso_auth.tokens.guardar_sesion.return_value = False

    with pytest.raises(AuthenticationError):
        caso_auth.servicio.login(caso_auth.credenciales)

    caso_auth.tokens.guardar_sesion.assert_called_once()


def test_refresh_rechazado_no_emite_access(caso_auth):
    """No emite tokens si la rotación persistente rechaza el refresh."""
    caso_auth.tokens.rotar.return_value = None

    with pytest.raises(AuthenticationError):
        caso_auth.servicio.refresh("refresh-invalido")

    caso_auth.emitir.assert_not_called()


def test_configuracion_invalida_no_consume_el_refresh(caso_auth, monkeypatch):
    """Una clave mal configurada se detecta antes de consumir el token vigente."""
    monkeypatch.setenv("JWT_SECRET", "corta")

    with pytest.raises(RuntimeError):
        caso_auth.servicio.refresh("refresh-vigente")

    caso_auth.tokens.rotar.assert_not_called()


def test_logout_delega_la_revocacion_por_hash(caso_auth):
    """Entrega el digest al cierre transaccional de la familia de sesiones."""
    token_hash = hashlib.sha256(b"refresh-de-prueba").hexdigest()

    caso_auth.servicio.logout("refresh-de-prueba")

    caso_auth.tokens.cerrar_sesion.assert_called_once_with(token_hash)


@pytest.mark.parametrize("existe", [False, True], ids=["desconocido", "ya-revocado"])
def test_logout_es_idempotente_para_tokens_no_activos(caso_auth, existe):
    """El cierre se delega por hash también si el token es desconocido o revocado."""
    if existe:
        caso_auth.tokens.obtener_refresh_token_por_hash.return_value = RefreshToken(
            UUID(int=2),
            "hash-de-prueba",
            caso_auth.usuario.id,
            caso_auth.ahora,
            revocado=True,
        )

    assert caso_auth.servicio.logout("refresh-de-prueba") is None

    caso_auth.tokens.cerrar_sesion.assert_called_once_with(
        hashlib.sha256(b"refresh-de-prueba").hexdigest()
    )


@pytest.fixture
def recuperacion_preparada(caso_auth, monkeypatch):
    """Aísla firma y envío para comprobar decisiones y privacidad del servicio."""
    token = "reset-token-privado"
    monkeypatch.setattr(auth_service, "crear_reset_token", Mock(return_value=token))
    monkeypatch.setattr(
        auth_service,
        "decodificar_reset_token",
        Mock(
            return_value={
                "jti": str(UUID(int=9)),
                "exp": int((caso_auth.ahora + timedelta(minutes=15)).timestamp()),
            }
        ),
    )
    correo = Mock()
    monkeypatch.setattr(auth_service, "enviar_recuperacion", correo)
    caso_auth.tokens.limitar.return_value = True
    caso_auth.tokens.preparar_recuperacion.return_value = True
    return SimpleNamespace(caso=caso_auth, correo=correo, token=token)


@pytest.mark.parametrize("error", [OSError, smtplib.SMTPException])
def test_fallo_smtp_conserva_respuesta_generica_y_no_registra_secretos(
    recuperacion_preparada, caplog, error
):
    """Ni el enlace ni el destinatario se filtran por el error del transporte."""
    caso = recuperacion_preparada.caso
    mensaje_sensible = f"{caso.usuario.email} {recuperacion_preparada.token}"
    recuperacion_preparada.correo.side_effect = error(mensaje_sensible)

    assert caso.servicio.solicitar_recuperacion(caso.usuario.email, "127.0.0.1") is None

    caso.tokens.preparar_recuperacion.assert_called_once()
    recuperacion_preparada.correo.assert_called_once_with(
        caso.usuario.email, recuperacion_preparada.token
    )
    assert "No se pudo entregar el correo de recuperación." in caplog.text
    assert caso.usuario.email not in caplog.text
    assert recuperacion_preparada.token not in caplog.text


def test_recuperacion_rechazada_al_persistir_no_envia_un_enlace_invalido(
    recuperacion_preparada,
):
    """Si cambia el estado de la cuenta entre lectura y guardado, no envía correo."""
    caso = recuperacion_preparada.caso
    caso.tokens.preparar_recuperacion.return_value = False

    assert caso.servicio.solicitar_recuperacion(caso.usuario.email, "127.0.0.1") is None

    caso.tokens.preparar_recuperacion.assert_called_once()
    recuperacion_preparada.correo.assert_not_called()
