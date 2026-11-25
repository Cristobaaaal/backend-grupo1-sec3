"""Repositorios reales y fábricas de datos para las pruebas de integración."""

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models import (
    CentroPokemon,
    Entrenador,
    Pokemon,
    RolUsuario,
    TipoPokemon,
    Usuario,
)
from app.infrastructure.database import get_db
from app.main import app
from app.repositories.centro_pokemon_repository import CentroPokemonRepository
from app.repositories.pokemon_repository import PokemonRepository
from app.repositories.registro_medico_repository import RegistroMedicoRepository
from app.repositories.trainer_repository import EntrenadorRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.schemas import CrearRegistroMedico
from app.security.passwords import hash_password
from tests.security_support import TEST_PASSWORD


@pytest.fixture
def api_client(clean_database):
    """Usa la API real; solo dirige la sesión a PostgreSQL de pruebas."""
    anteriores = app.dependency_overrides.copy()

    def sesion_de_prueba():
        with Session(clean_database) as session:
            yield session

    app.dependency_overrides[get_db] = sesion_de_prueba
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(anteriores)


@pytest.fixture(scope="session")
def hash_de_password_de_prueba():
    """Calcula un hash Argon2 real reutilizable para las cuentas de las fixtures."""
    return hash_password(TEST_PASSWORD)


@pytest.fixture
def crear_usuario(db_session, hash_de_password_de_prueba):
    """Prepara cuentas por rol con el repositorio real, sin permitirlo por el DTO."""

    def crear(email="ash@example.com", rol=RolUsuario.ENTRENADOR, **cambios):
        datos = {
            "id": uuid4(),
            "email": email,
            "password_hash": hash_de_password_de_prueba,
            "nombre_completo": "Usuario Pruebas",
            "rol": rol,
        }
        datos.update(cambios)
        return UsuarioRepository(db_session).crear(Usuario(**datos))

    return crear


@pytest.fixture
def login(api_client):
    """Obtiene tokens por HTTP con el login real, sin sustituir JWT ni servicios."""

    def autenticar(usuario, password=TEST_PASSWORD):
        respuesta = api_client.post(
            "/auth/login", json={"email": usuario.email, "password": password}
        )
        assert respuesta.status_code == 200, respuesta.text
        return respuesta.json()

    return autenticar


@pytest.fixture
def repositorios(db_session):
    """Construye los cuatro repositorios sobre una sesión de PostgreSQL."""
    return SimpleNamespace(
        entrenadores=EntrenadorRepository(db_session),
        pokemones=PokemonRepository(db_session),
        centros=CentroPokemonRepository(db_session),
        registros=RegistroMedicoRepository(db_session),
    )


@pytest.fixture
def crear_entrenador(repositorios):
    """Guarda un entrenador real con datos reproducibles y un UUID nuevo."""

    def crear(nombre="Ash"):
        return repositorios.entrenadores.save(
            Entrenador(uuid4(), nombre, 10, "Kanto", 3)
        )

    return crear


@pytest.fixture
def crear_pokemon(repositorios):
    """Guarda un Pokémon real; permite variar relaciones y orden de paginación."""

    def crear(
        nombre="Pikachu",
        tipo=TipoPokemon.ELECTRICO,
        nivel=10,
        entrenador_id=None,
        pokemon_id=None,
    ):
        return repositorios.pokemones.save(
            Pokemon(pokemon_id or uuid4(), nombre, tipo, nivel, 40, entrenador_id)
        )

    return crear


@pytest.fixture
def crear_centro(repositorios):
    """Guarda un centro operativo con capacidad válida."""

    def crear(ciudad="Temuco"):
        return repositorios.centros.save(
            CentroPokemon(uuid4(), "Centro Norte", ciudad, 10, True)
        )

    return crear


@pytest.fixture
def historial_medico(repositorios, crear_pokemon, crear_centro):
    """Guarda el historial de un Pokémon dado de alta en un centro real."""
    pokemon = crear_pokemon()
    centro = crear_centro()
    registro = repositorios.registros.guardar(
        CrearRegistroMedico(
            pokemon_id=pokemon.id,
            centro_id=centro.id,
            diagnostico="Agotamiento",
            fecha_ingreso=date(2026, 1, 1),
            estado="DADO_DE_ALTA",
            costo=5000,
        )
    )
    return SimpleNamespace(pokemon=pokemon, centro=centro, registro=registro)
