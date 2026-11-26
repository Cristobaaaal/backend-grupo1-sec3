"""Protección del entrenador y sus relaciones con Pokémon."""

from uuid import UUID

import pytest

from app.core.exceptions import ConflictError, NotFoundException
from app.domain.models import Entrenador, Pokemon, TipoPokemon
from app.schemas.schemas import CrearEntrenador

pytestmark = pytest.mark.unit


def test_actualizar_conserva_identidad_y_guarda_los_nuevos_datos(caso_trainer):
    """Actualizar conserva identidad y guarda los nuevos datos."""
    datos = CrearEntrenador(
        nombre="Ash Ketchum",
        nivel_experiencia=20,
        region_origen="Johto",
        medallas_obtenidas=4,
    )
    esperado = Entrenador(caso_trainer.entrenador.id, "Ash Ketchum", 20, "Johto", 4)
    caso_trainer.repo.update.return_value = esperado
    resultado = caso_trainer.servicio.actualizar_entrenador(
        caso_trainer.entrenador.id, datos
    )
    assert resultado == esperado
    caso_trainer.repo.update.assert_called_once_with(
        caso_trainer.entrenador.id, esperado
    )
    caso_trainer.repo.save.assert_not_called()


def test_eliminar_rechaza_entrenador_con_pokemon_asignado(caso_trainer):
    """Eliminar rechaza entrenador con pokemon asignado."""
    caso_trainer.pokemones.get_by_entrenador_id.return_value = [
        Pokemon(
            UUID(int=2),
            "Pikachu",
            TipoPokemon.ELECTRICO,
            10,
            40,
            caso_trainer.entrenador.id,
        )
    ]
    with pytest.raises(ConflictError, match="Pokémon asignados"):
        caso_trainer.servicio.eliminar_entrenador(caso_trainer.entrenador.id)
    caso_trainer.pokemones.get_by_entrenador_id.assert_called_once_with(
        caso_trainer.entrenador.id
    )
    caso_trainer.repo.delete.assert_not_called()


def test_eliminar_permite_entrenador_sin_pokemones(caso_trainer):
    """Eliminar permite entrenador sin pokemones."""
    caso_trainer.pokemones.get_by_entrenador_id.return_value = []
    assert caso_trainer.servicio.eliminar_entrenador(caso_trainer.entrenador.id) is None
    caso_trainer.repo.delete.assert_called_once_with(caso_trainer.entrenador.id)


def test_eliminar_rechaza_id_inexistente_sin_consultar_relaciones(caso_trainer):
    """Eliminar rechaza id inexistente sin consultar relaciones."""
    caso_trainer.repo.get_by_id.return_value = None
    with pytest.raises(NotFoundException) as error:
        caso_trainer.servicio.eliminar_entrenador(caso_trainer.entrenador.id)
    assert str(caso_trainer.entrenador.id) in error.value.message
    caso_trainer.pokemones.get_by_entrenador_id.assert_not_called()
    caso_trainer.repo.delete.assert_not_called()
