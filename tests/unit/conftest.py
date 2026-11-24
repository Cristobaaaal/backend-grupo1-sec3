"""Fixtures unitarias inspiradas en la actividad de Student.

Cada caso recibe datos y repositorios nuevos. create_autospec limita los dobles
a la interfaz real del repositorio y comprueba las firmas de sus métodos.
No se instancian sesiones SQLAlchemy ni se consulta una base de datos.
"""

from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, create_autospec
from uuid import UUID

import pytest
from sqlalchemy.engine import Engine

from app.domain.models import (
    CentroPokemon,
    Entrenador,
    EstadoAtencion,
    Pokemon,
    RegistroMedico,
    TipoPokemon,
)
from app.repositories.centro_pokemon_repository import CentroPokemonRepository
from app.repositories.pokemon_repository import PokemonRepository
from app.repositories.registro_medico_repository import RegistroMedicoRepository
from app.repositories.trainer_repository import EntrenadorRepository
from app.schemas.schemas import CrearPokemon, CrearRegistroMedico
from app.services.centro_pokemon_service import CentroPokemonService
from app.services.pokemon_service import PokemonService
from app.services.registro_medico_service import RegistroMedicoService
from app.services.trainer_service import EntrenadorService


@pytest.fixture(autouse=True)
def impedir_conexion_a_bd(monkeypatch):
    """Falla si una prueba unitaria intenta abrir una conexión real a BD."""

    def rechazar_conexion(*args, **kwargs):
        raise AssertionError("Una prueba unitaria no debe conectarse a la BD.")

    monkeypatch.setattr(Engine, "connect", rechazar_conexion)


@pytest.fixture
def caso_centro_pokemon():
    """Prepara un centro operativo, un registro y repositorios simulados."""
    caso_centro_pokemon = SimpleNamespace()
    caso_centro_pokemon.centros = create_autospec(
        CentroPokemonRepository, instance=True, spec_set=True
    )
    caso_centro_pokemon.registros = create_autospec(
        RegistroMedicoRepository, instance=True, spec_set=True
    )
    caso_centro_pokemon.servicio = CentroPokemonService(
        caso_centro_pokemon.centros, caso_centro_pokemon.registros
    )
    caso_centro_pokemon.centro = CentroPokemon(
        UUID(int=1), "Centro Norte", "Temuco", 10, True
    )
    caso_centro_pokemon.centros.get_by_id.return_value = caso_centro_pokemon.centro
    caso_centro_pokemon.registro = RegistroMedico(
        UUID(int=2),
        UUID(int=3),
        caso_centro_pokemon.centro.id,
        "Agotamiento",
        date(2026, 1, 1),
        EstadoAtencion.EN_TRATAMIENTO,
        5000,
    )
    return caso_centro_pokemon


@pytest.fixture
def caso_pokemon():
    """Prepara un Pokémon libre y un entrenador con repositorios simulados."""
    caso_pokemon = SimpleNamespace()
    caso_pokemon.repo = create_autospec(PokemonRepository, instance=True, spec_set=True)
    caso_pokemon.entrenadores = create_autospec(
        EntrenadorRepository, instance=True, spec_set=True
    )
    caso_pokemon.registros = create_autospec(
        RegistroMedicoRepository, instance=True, spec_set=True
    )
    caso_pokemon.servicio = PokemonService(
        caso_pokemon.repo, caso_pokemon.entrenadores, caso_pokemon.registros
    )
    caso_pokemon.entrenador = Entrenador(UUID(int=1), "Ash", 10, "Kanto", 3)
    caso_pokemon.pokemon = Pokemon(
        UUID(int=2), "Pikachu", TipoPokemon.ELECTRICO, 10, 40
    )
    caso_pokemon.repo.get_by_id.return_value = caso_pokemon.pokemon
    caso_pokemon.entrenadores.get_by_id.return_value = caso_pokemon.entrenador
    caso_pokemon.datos = CrearPokemon(
        nombre="Pikachu", tipo_principal="ELECTRICO", nivel=10, puntos_vida=40
    )
    return caso_pokemon


@pytest.fixture
def caso_registro_medico(monkeypatch):
    """Prepara un ingreso válido y fija la fecha sin esperas ni cambios globales."""
    caso_registro_medico = SimpleNamespace()
    caso_registro_medico.repo = create_autospec(
        RegistroMedicoRepository, instance=True, spec_set=True
    )
    caso_registro_medico.pokemones = create_autospec(
        PokemonRepository, instance=True, spec_set=True
    )
    caso_registro_medico.centros = create_autospec(
        CentroPokemonRepository, instance=True, spec_set=True
    )
    caso_registro_medico.servicio = RegistroMedicoService(
        caso_registro_medico.repo,
        caso_registro_medico.pokemones,
        caso_registro_medico.centros,
    )
    caso_registro_medico.hoy = date(2026, 1, 15)
    reloj = Mock(wraps=date)
    monkeypatch.setattr("app.services.registro_medico_service.date", reloj)
    reloj.today.return_value = caso_registro_medico.hoy
    caso_registro_medico.pokemon = Pokemon(
        UUID(int=1), "Pikachu", TipoPokemon.ELECTRICO, 10, 40
    )
    caso_registro_medico.centro = CentroPokemon(
        UUID(int=2), "Centro Norte", "Temuco", 10, True
    )
    caso_registro_medico.pokemones.get_by_id.return_value = caso_registro_medico.pokemon
    caso_registro_medico.centros.get_by_id.return_value = caso_registro_medico.centro
    caso_registro_medico.datos = CrearRegistroMedico(
        pokemon_id=caso_registro_medico.pokemon.id,
        centro_id=caso_registro_medico.centro.id,
        diagnostico="Agotamiento",
        fecha_ingreso=caso_registro_medico.hoy,
        estado="EN_TRATAMIENTO",
        costo=5000,
    )
    caso_registro_medico.registro = RegistroMedico(
        UUID(int=3),
        caso_registro_medico.pokemon.id,
        caso_registro_medico.centro.id,
        "Agotamiento",
        caso_registro_medico.hoy,
        EstadoAtencion.EN_TRATAMIENTO,
        5000,
    )
    return caso_registro_medico


@pytest.fixture
def caso_trainer():
    """Prepara un entrenador existente y repositorios simulados."""
    caso_trainer = SimpleNamespace()
    caso_trainer.repo = create_autospec(
        EntrenadorRepository, instance=True, spec_set=True
    )
    caso_trainer.pokemones = create_autospec(
        PokemonRepository, instance=True, spec_set=True
    )
    caso_trainer.servicio = EntrenadorService(caso_trainer.repo, caso_trainer.pokemones)
    caso_trainer.entrenador = Entrenador(UUID(int=1), "Ash", 10, "Kanto", 3)
    caso_trainer.repo.get_by_id.return_value = caso_trainer.entrenador
    return caso_trainer


@pytest.fixture
def pokemon_payload():
    """Fábrica de entradas válidas; cada prueba modifica solo el campo que evalúa."""

    def build(**cambios):
        datos = {
            "nombre": "Pikachu",
            "tipo_principal": "ELECTRICO",
            "nivel": 10,
            "puntos_vida": 40,
        }
        datos.update(cambios)
        return datos

    return build
