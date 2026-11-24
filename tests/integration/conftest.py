"""Repositorios reales y fábricas de datos para las pruebas de integración."""

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.domain.models import CentroPokemon, Entrenador, Pokemon, TipoPokemon
from app.repositories.centro_pokemon_repository import CentroPokemonRepository
from app.repositories.pokemon_repository import PokemonRepository
from app.repositories.registro_medico_repository import RegistroMedicoRepository
from app.repositories.trainer_repository import EntrenadorRepository
from app.schemas.schemas import CrearRegistroMedico


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
