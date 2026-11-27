"""Reglas de borrado de centros con pacientes e historial clínico."""

from uuid import UUID

import pytest

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundException
from app.domain.models import EstadoAtencion

pytestmark = pytest.mark.unit


def test_eliminar_rechaza_centro_con_pacientes_en_tratamiento(caso_centro_pokemon):
    """Eliminar rechaza centro con pacientes en tratamiento."""
    caso_centro_pokemon.registros.obtener_todos.return_value = [
        caso_centro_pokemon.registro
    ]
    with pytest.raises(BusinessRuleError, match="en tratamiento"):
        caso_centro_pokemon.servicio.eliminar_centro_pokemon(
            caso_centro_pokemon.centro.id
        )
    caso_centro_pokemon.centros.delete.assert_not_called()


def test_eliminar_rechaza_centro_con_historial_aunque_tenga_alta(caso_centro_pokemon):
    """Eliminar rechaza centro con historial aunque tenga alta."""
    caso_centro_pokemon.registro.estado = EstadoAtencion.DADO_DE_ALTA
    caso_centro_pokemon.registros.obtener_todos.return_value = [
        caso_centro_pokemon.registro
    ]
    with pytest.raises(ConflictError, match="históricos"):
        caso_centro_pokemon.servicio.eliminar_centro_pokemon(
            caso_centro_pokemon.centro.id
        )
    caso_centro_pokemon.centros.delete.assert_not_called()


def test_eliminar_permite_centro_sin_registros(caso_centro_pokemon):
    """Eliminar permite centro sin registros."""
    caso_centro_pokemon.registros.obtener_todos.return_value = []
    assert (
        caso_centro_pokemon.servicio.eliminar_centro_pokemon(
            caso_centro_pokemon.centro.id
        )
        is None
    )
    caso_centro_pokemon.centros.delete.assert_called_once_with(
        caso_centro_pokemon.centro.id
    )


def test_pacientes_de_otro_centro_no_impiden_el_borrado(caso_centro_pokemon):
    """Pacientes de otro centro no impiden el borrado."""
    caso_centro_pokemon.registro.centro_id = UUID(int=4)
    caso_centro_pokemon.registros.obtener_todos.return_value = [
        caso_centro_pokemon.registro
    ]
    caso_centro_pokemon.servicio.eliminar_centro_pokemon(caso_centro_pokemon.centro.id)
    caso_centro_pokemon.centros.delete.assert_called_once_with(
        caso_centro_pokemon.centro.id
    )


def test_eliminar_rechaza_centro_inexistente_sin_borrar(caso_centro_pokemon):
    """Eliminar rechaza centro inexistente sin borrar."""
    caso_centro_pokemon.centros.get_by_id.return_value = None
    with pytest.raises(NotFoundException) as error:
        caso_centro_pokemon.servicio.eliminar_centro_pokemon(
            caso_centro_pokemon.centro.id
        )
    assert str(caso_centro_pokemon.centro.id) in error.value.message
    caso_centro_pokemon.registros.obtener_todos.assert_not_called()
    caso_centro_pokemon.centros.delete.assert_not_called()
