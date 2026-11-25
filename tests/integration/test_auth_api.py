"""Autenticación y permisos por HTTP con JWT, Argon2 y PostgreSQL reales."""

import hashlib
from datetime import UTC, datetime
from uuid import UUID

import jwt
import pytest
from sqlalchemy import func, select

from app.domain.models import RolUsuario
from app.infrastructure.models import RefreshTokenORM, UsuarioORM
from app.repositories.token_repository import TokenRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.security.passwords import verify_password
from app.security.tokens import crear_access_token, decodificar_access_token
from tests.security_support import (
    TEST_JWT_SECRET,
    TEST_PASSWORD,
    access_payload,
    alterar_firma,
)

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("rol_solicitado", [None, "ADMIN", "VETERINARIO"])
def test_registro_guarda_argon2_y_no_permite_autoasignar_privilegios(
    api_client, db_session, rol_solicitado
):
    """El alta pública crea ENTRENADOR y el DTO no expone credenciales."""
    datos = {
        "email": "ASH@example.com",
        "nombre_completo": "Ash",
        "password": TEST_PASSWORD,
    }
    if rol_solicitado is not None:
        datos["rol"] = rol_solicitado

    respuesta = api_client.post("/auth/register", json=datos)

    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"id", "email", "nombre_completo", "rol", "activo"}
    assert cuerpo["rol"] == "ENTRENADOR"
    usuario = UsuarioRepository(db_session).obtener_por_id(UUID(cuerpo["id"]))
    assert usuario.email == "ash@example.com"
    assert usuario.rol == RolUsuario.ENTRENADOR
    assert usuario.password_hash.startswith("$argon2id$")
    assert usuario.password_hash != TEST_PASSWORD
    assert verify_password(TEST_PASSWORD, usuario.password_hash)


def test_registro_duplicado_devuelve_409_y_conserva_una_sola_cuenta(
    api_client, db_session, crear_usuario
):
    """El servicio rechaza el mismo correo aunque cambien sus mayúsculas."""
    original = crear_usuario()

    respuesta = api_client.post(
        "/auth/register",
        json={
            "email": "ASH@example.com",
            "nombre_completo": "Otro Nombre",
            "password": TEST_PASSWORD,
        },
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "RESOURCE_CONFLICT"
    assert db_session.scalar(select(func.count()).select_from(UsuarioORM)) == 1
    assert UsuarioRepository(db_session).obtener_por_id(original.id) == original


@pytest.mark.parametrize("password", ["", "a" * 11], ids=["vacia", "once-caracteres"])
def test_registro_rechaza_password_menor_al_minimo_sin_guardar_usuario(
    api_client, db_session, password
):
    """La política mínima de doce caracteres se aplica antes de persistir."""
    respuesta = api_client.post(
        "/auth/register",
        json={
            "email": "ash@example.com",
            "nombre_completo": "Ash",
            "password": password,
        },
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "VALIDATION_ERROR"
    assert db_session.scalar(select(func.count()).select_from(UsuarioORM)) == 0


def test_login_emite_jwt_valido_persiste_hash_de_refresh_y_permite_me(
    api_client, db_session, crear_usuario, login
):
    """Comprueba identidad, JWT, persistencia del refresh y DTO público de /me."""
    usuario = crear_usuario()

    tokens = login(usuario)
    claims = decodificar_access_token(tokens["access_token"])
    respuesta = api_client.get(
        "/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )

    assert tokens["token_type"] == "bearer"
    assert claims["sub"] == str(usuario.id)
    assert claims["type"] == "access"
    assert respuesta.status_code == 200
    assert respuesta.json()["id"] == str(usuario.id)
    assert set(respuesta.json()) == {"id", "email", "nombre_completo", "rol", "activo"}
    token_hash = hashlib.sha256(tokens["refresh_token"].encode()).hexdigest()
    guardado = TokenRepository(db_session).obtener_refresh_token_por_hash(token_hash)
    assert guardado.usuario_id == usuario.id
    assert guardado.revocado is False
    assert guardado.token_hash != tokens["refresh_token"]
    assert (guardado.expira_en - guardado.creado_en).days == 7


def test_credenciales_erroneas_son_genericas_y_no_crean_tokens(
    api_client, db_session, crear_usuario
):
    """Correo desconocido y password incorrecta producen el mismo error público."""
    usuario = crear_usuario()
    respuestas = [
        api_client.post(
            "/auth/login", json={"email": correo, "password": "Incorrecta123!"}
        )
        for correo in [usuario.email, "desconocido@example.com"]
    ]

    for respuesta in respuestas:
        assert respuesta.status_code == 401
        assert respuesta.headers["WWW-Authenticate"] == "Bearer"
        assert respuesta.json()["error"]["code"] == "AUTHENTICATION_ERROR"
        assert "access_token" not in respuesta.json()
        assert "refresh_token" not in respuesta.json()
    assert respuestas[0].json() == respuestas[1].json()
    assert db_session.scalar(select(func.count()).select_from(RefreshTokenORM)) == 0


def test_cinco_fallos_persisten_bloqueo_y_rechazan_incluso_la_clave_correcta(
    api_client, db_session, crear_usuario
):
    """El bloqueo es efectivo y queda guardado; no se necesitan esperas."""
    usuario = crear_usuario()
    for _ in range(5):
        respuesta = api_client.post(
            "/auth/login",
            json={
                "email": usuario.email,
                "password": "Incorrecta123!",
            },
        )
        assert respuesta.status_code == 401

    guardado = UsuarioRepository(db_session).obtener_por_id(usuario.id)
    assert guardado.intentos_fallidos == 5
    assert guardado.bloqueado_hasta > datetime.now(UTC).replace(tzinfo=None)
    respuesta = api_client.post(
        "/auth/login",
        json={
            "email": usuario.email,
            "password": TEST_PASSWORD,
        },
    )
    assert respuesta.status_code == 401
    assert db_session.scalar(select(func.count()).select_from(RefreshTokenORM)) == 0


def test_login_tras_caducar_bloqueo_limpia_contador_y_fecha(
    db_session, crear_usuario, login
):
    """Una fecha de bloqueo pasada permite login y restablece el estado en BD."""
    usuario = crear_usuario(intentos_fallidos=5, bloqueado_hasta=datetime(2000, 1, 1))

    tokens = login(usuario)
    guardado = UsuarioRepository(db_session).obtener_por_id(usuario.id)

    assert tokens["access_token"]
    assert guardado.intentos_fallidos == 0
    assert guardado.bloqueado_hasta is None


def test_cuenta_inactiva_no_puede_iniciar_sesion(api_client, db_session, crear_usuario):
    """El estado inactivo se aplica aunque la contraseña sea correcta."""
    usuario = crear_usuario(activo=False)

    respuesta = api_client.post(
        "/auth/login",
        json={
            "email": usuario.email,
            "password": TEST_PASSWORD,
        },
    )

    assert respuesta.status_code == 401
    assert db_session.scalar(select(func.count()).select_from(RefreshTokenORM)) == 0


@pytest.mark.parametrize(
    "ruta",
    [
        "/auth/me",
        "/entrenadores/",
        "/pokemones/",
        "/centros-pokemon/",
        "/registros-medicos/",
    ],
    ids=["me", "entrenadores", "pokemones", "centros", "registros"],
)
def test_rutas_privadas_rechazan_ausencia_de_token(api_client, ruta):
    """Todos los recursos privados rechazan peticiones anónimas con 401."""
    respuesta = api_client.get(ruta)

    assert respuesta.status_code == 401
    assert respuesta.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "caso", ["manipulado", "vencido", "otro-proposito", "otro-algoritmo", "ilegible"]
)
def test_me_rechaza_jwt_invalido_con_401(api_client, crear_usuario, caso):
    """La validación JWT real se traduce en un rechazo HTTP uniforme."""
    usuario = crear_usuario()
    claims = access_payload(sub=str(usuario.id))
    algoritmo = "HS256"
    if caso == "vencido":
        claims.update(iat=datetime(2000, 1, 1, tzinfo=UTC), exp=1)
    elif caso == "otro-proposito":
        claims["type"] = "password_reset"
    elif caso == "otro-algoritmo":
        algoritmo = "HS384"
    token = jwt.encode(claims, TEST_JWT_SECRET, algorithm=algoritmo)
    if caso == "manipulado":
        token = alterar_firma(token)
    elif caso == "ilegible":
        token = "no-es-un-jwt"

    respuesta = api_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert respuesta.status_code == 401
    assert respuesta.headers["WWW-Authenticate"] == "Bearer"
    assert respuesta.json()["error"]["code"] == "HTTP_ERROR"


@pytest.mark.parametrize("caso", ["usuario-inexistente", "usuario-inactivo"])
def test_firma_valida_no_habilita_una_identidad_inexistente_o_inactiva(
    api_client, crear_usuario, caso
):
    """El usuario se vuelve a consultar en BD después de validar la firma."""
    if caso == "usuario-inactivo":
        usuario_id = crear_usuario(activo=False).id
    else:
        usuario_id = UUID(int=999)
    token = crear_access_token(usuario_id)

    respuesta = api_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert respuesta.status_code == 401


@pytest.mark.parametrize(
    ("rol", "esperado"),
    [
        (None, 401),
        (RolUsuario.ENTRENADOR, 403),
        (RolUsuario.VETERINARIO, 403),
        (RolUsuario.ADMIN, 204),
    ],
    ids=["sin-token", "entrenador", "veterinario", "admin"],
)
def test_misma_eliminacion_distingue_autenticacion_y_permiso(
    api_client,
    db_session,
    repositorios,
    crear_centro,
    crear_usuario,
    login,
    rol,
    esperado,
):
    """Solo ADMIN elimina; los rechazos conservan el centro en PostgreSQL."""
    centro = crear_centro()
    headers = {}
    if rol is not None:
        tokens = login(crear_usuario(rol=rol))
        headers["Authorization"] = f"Bearer {tokens['access_token']}"

    respuesta = api_client.delete(f"/centros-pokemon/{centro.id}", headers=headers)

    assert respuesta.status_code == esperado, respuesta.text
    db_session.expire_all()
    guardado = repositorios.centros.get_by_id(centro.id)
    assert (guardado is None) == (esperado == 204)


def test_veterinario_puede_crear_un_centro(
    api_client, repositorios, crear_usuario, login
):
    """VETERINARIO tiene permiso de creación, aunque no tenga permiso de borrado."""
    tokens = login(crear_usuario(rol=RolUsuario.VETERINARIO))

    respuesta = api_client.post(
        "/centros-pokemon/",
        json={
            "nombre": "Centro Pruebas",
            "ciudad": "Temuco",
            "capacidad_maxima": 10,
        },
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert respuesta.status_code == 201, respuesta.text
    guardado = repositorios.centros.get_by_id(UUID(respuesta.json()["id"]))
    assert guardado.nombre == "Centro Pruebas"
    assert guardado.capacidad_maxima == 10


def test_logout_revoca_solo_su_refresh_y_es_idempotente(
    api_client, db_session, crear_usuario, login
):
    """Logout persiste revocación; conserva otra sesión y la ventana del access."""
    usuario = crear_usuario()
    primera = login(usuario)
    segunda = login(usuario)

    for _ in range(2):
        respuesta = api_client.post(
            "/auth/logout", json={"refresh_token": primera["refresh_token"]}
        )
        assert respuesta.status_code == 204

    repositorio = TokenRepository(db_session)
    primer_hash = hashlib.sha256(primera["refresh_token"].encode()).hexdigest()
    segundo_hash = hashlib.sha256(segunda["refresh_token"].encode()).hexdigest()
    assert repositorio.obtener_refresh_token_por_hash(primer_hash).revocado is True
    assert repositorio.obtener_refresh_token_por_hash(segundo_hash).revocado is False
    respuesta = api_client.get(
        "/auth/me", headers={"Authorization": f"Bearer {primera['access_token']}"}
    )
    assert respuesta.status_code == 200
