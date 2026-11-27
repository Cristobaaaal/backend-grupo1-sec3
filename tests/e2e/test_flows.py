"""Los tres E2E de la pauta: negocio, recuperación y permisos diferenciados."""

from urllib.parse import urlsplit
from uuid import UUID

import pytest

from tests.security_support import TEST_PASSWORD
from tests.smtp_capture import enlace_del_correo, token_del_correo

pytestmark = pytest.mark.e2e


def registrar(client, email):
    respuesta = client.post(
        "/auth/register",
        json={
            "email": email,
            "nombre_completo": "Usuario E2E",
            "password": TEST_PASSWORD,
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["rol"] == "ENTRENADOR"
    assert "password" not in respuesta.json()
    assert "password_hash" not in respuesta.json()
    return respuesta.json()


def login(client, email, password=TEST_PASSWORD):
    respuesta = client.post("/auth/login", json={"email": email, "password": password})
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def bearer(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_acceso_negocio_y_logout_impide_renovar(e2e_app):
    """Registro → login → creación/consulta protegida → rotación → logout → rechazo."""
    client = e2e_app.client
    usuario = registrar(client, "negocio-e2e@example.com")
    tokens = login(client, usuario["email"])
    headers = bearer(tokens)

    entrenador = client.post(
        "/entrenadores/",
        headers=headers,
        json={
            "nombre": "Ash E2E",
            "nivel_experiencia": 10,
            "region_origen": "Kanto",
            "medallas_obtenidas": 3,
        },
    )
    assert entrenador.status_code == 201, entrenador.text
    entrenador_id = entrenador.json()["id"]
    UUID(entrenador_id)
    pokemon = client.post(
        "/pokemones/",
        headers=headers,
        json={
            "nombre": "Pikachu",
            "tipo_principal": "ELECTRICO",
            "nivel": 10,
            "puntos_vida": 40,
            "entrenador_id": entrenador_id,
        },
    )
    assert pokemon.status_code == 201, pokemon.text
    pokemon_id = pokemon.json()["id"]
    consulta = client.get(f"/pokemones/{pokemon_id}", headers=headers)
    assert consulta.status_code == 200
    assert consulta.json()["id"] == pokemon_id
    assert consulta.json()["nombre"] == "Pikachu"
    assert consulta.json()["entrenador_id"] == entrenador_id

    rechazado = client.patch(
        f"/pokemones/{pokemon_id}/asignar/{entrenador_id}", headers=headers
    )
    assert rechazado.status_code == 400
    assert rechazado.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"
    assert (
        client.get(f"/pokemones/{pokemon_id}", headers=headers).json()["entrenador_id"]
        == entrenador_id
    )

    renovacion = client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert renovacion.status_code == 200, renovacion.text
    nuevos = renovacion.json()
    assert nuevos["refresh_token"] != tokens["refresh_token"]
    actual = client.get("/auth/me", headers=bearer(nuevos))
    assert actual.status_code == 200
    assert actual.json()["id"] == usuario["id"]
    cierre = client.post(
        "/auth/logout", json={"refresh_token": nuevos["refresh_token"]}
    )
    assert cierre.status_code == 204
    assert cierre.content == b""
    respuesta = client.post(
        "/auth/refresh", json={"refresh_token": nuevos["refresh_token"]}
    )
    assert respuesta.status_code == 401
    assert "access_token" not in respuesta.json()
    assert client.get("/auth/me", headers=bearer(nuevos)).status_code == 401


def test_recuperacion_por_correo_consumo_unico_e_invalidacion_de_sesiones(e2e_app):
    """Correo real → cambio → rechazo de segundo uso/clave anterior → nueva sesión."""
    client = e2e_app.client
    usuario = registrar(client, "recuperacion-e2e@example.com")
    anteriores = [login(client, usuario["email"]), login(client, usuario["email"])]
    solicitud = client.post("/auth/forgot-password", json={"email": usuario["email"]})
    assert solicitud.status_code == 202
    assert set(solicitud.json()) == {"message"}

    enlace = enlace_del_correo(e2e_app.smtp, usuario["email"])
    url = urlsplit(enlace)
    base = urlsplit(e2e_app.base_url)
    assert (url.scheme, url.hostname, url.port) == (
        base.scheme,
        base.hostname,
        base.port,
    )
    assert url.path == "/auth/reset-password"
    formulario = client.get(url._replace(fragment="").geturl())
    assert formulario.status_code == 200
    assert formulario.headers["Cache-Control"] == "no-store"
    assert formulario.headers["Referrer-Policy"] == "no-referrer"
    token = token_del_correo(e2e_app.smtp, usuario["email"])
    nueva_password = "NuevaClaveE2ESegura123!"
    cambio = client.post(
        "/auth/reset-password", json={"token": token, "password": nueva_password}
    )
    assert cambio.status_code == 200, cambio.text
    assert (
        client.post(
            "/auth/reset-password",
            json={
                "token": token,
                "password": "OtraClaveE2ESegura123!",
            },
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/auth/login",
            json={
                "email": usuario["email"],
                "password": TEST_PASSWORD,
            },
        ).status_code
        == 401
    )
    for sesion in anteriores:
        assert client.get("/auth/me", headers=bearer(sesion)).status_code == 401
        assert (
            client.post(
                "/auth/refresh", json={"refresh_token": sesion["refresh_token"]}
            ).status_code
            == 401
        )
    nuevos = login(client, usuario["email"], nueva_password)
    actual = client.get("/auth/me", headers=bearer(nuevos))
    assert actual.status_code == 200
    assert actual.json()["id"] == usuario["id"]


def test_permisos_rechazan_anonimo_y_entrenador_y_permiten_admin(e2e_app, cuenta_admin):
    """La misma creación devuelve 401, 403 y 201 según identidad y permisos."""
    client = e2e_app.client
    datos = {"nombre": "Centro E2E", "ciudad": "Temuco", "capacidad_maxima": 10}
    anonimo = client.post("/centros-pokemon/", json=datos)
    assert anonimo.status_code == 401
    assert anonimo.headers["WWW-Authenticate"] == "Bearer"

    entrenador = registrar(client, "permisos-e2e@example.com")
    basicos = login(client, entrenador["email"])
    sin_permiso = client.post("/centros-pokemon/", json=datos, headers=bearer(basicos))
    assert sin_permiso.status_code == 403
    antes = client.get("/centros-pokemon/", headers=bearer(basicos))
    assert antes.status_code == 200
    assert antes.json() == []

    autorizados = login(client, cuenta_admin.email)
    permitido = client.post(
        "/centros-pokemon/", json=datos, headers=bearer(autorizados)
    )
    assert permitido.status_code == 201, permitido.text
    centro_id = permitido.json()["id"]
    consulta = client.get(f"/centros-pokemon/{centro_id}", headers=bearer(autorizados))
    assert consulta.status_code == 200
    assert consulta.json()["nombre"] == "Centro E2E"
    assert consulta.json()["capacidad_maxima"] == 10
    listado = client.get("/centros-pokemon/", headers=bearer(autorizados))
    assert listado.status_code == 200
    assert [centro["id"] for centro in listado.json()] == [centro_id]
