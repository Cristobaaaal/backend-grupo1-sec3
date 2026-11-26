"""Admisión de pacientes con repositorios dobles y fecha controlada."""

from datetime import timedelta

import pytest

from app.core.exceptions import BusinessRuleError, NotFoundException
from app.domain.models import (
    EstadoAtencion,
)

pytestmark = pytest.mark.unit


def test_crear_admite_paciente_en_centro_operativo_con_fecha_actual(
    caso_registro_medico,
):
    """Crear admite paciente en centro operativo con fecha actual."""
    caso_registro_medico.repo.guardar.return_value = caso_registro_medico.registro
    resultado = caso_registro_medico.servicio.crear_registro(caso_registro_medico.datos)
    assert resultado.pokemon_id == caso_registro_medico.pokemon.id
    assert resultado.centro_id == caso_registro_medico.centro.id
    assert resultado.fecha_ingreso == caso_registro_medico.hoy
    assert resultado.estado == EstadoAtencion.EN_TRATAMIENTO
    assert resultado.costo == 5000
    caso_registro_medico.repo.guardar.assert_called_once_with(
        caso_registro_medico.datos
    )


def test_crear_rechaza_pokemon_inexistente_sin_guardar(caso_registro_medico):
    """Crear rechaza pokemon inexistente sin guardar."""
    caso_registro_medico.pokemones.get_by_id.return_value = None
    with pytest.raises(NotFoundException) as error:
        caso_registro_medico.servicio.crear_registro(caso_registro_medico.datos)
    assert str(caso_registro_medico.pokemon.id) in error.value.message
    caso_registro_medico.repo.guardar.assert_not_called()


def test_crear_rechaza_centro_inexistente_sin_guardar(caso_registro_medico):
    """Crear rechaza centro inexistente sin guardar."""
    caso_registro_medico.centros.get_by_id.return_value = None
    with pytest.raises(NotFoundException) as error:
        caso_registro_medico.servicio.crear_registro(caso_registro_medico.datos)
    assert str(caso_registro_medico.centro.id) in error.value.message
    caso_registro_medico.repo.guardar.assert_not_called()


def test_crear_rechaza_centro_fuera_de_servicio(caso_registro_medico):
    """Crear rechaza centro fuera de servicio."""
    caso_registro_medico.centro.en_servicio = False
    with pytest.raises(BusinessRuleError, match="no esta en servicio"):
        caso_registro_medico.servicio.crear_registro(caso_registro_medico.datos)
    caso_registro_medico.repo.guardar.assert_not_called()


def test_crear_rechaza_fecha_futura_sin_guardar(caso_registro_medico):
    """Crear rechaza fecha futura sin guardar."""
    caso_registro_medico.datos.fecha_ingreso = caso_registro_medico.hoy + timedelta(
        days=1
    )
    with pytest.raises(BusinessRuleError, match="fecha futura"):
        caso_registro_medico.servicio.crear_registro(caso_registro_medico.datos)
    caso_registro_medico.repo.guardar.assert_not_called()


def test_actualizar_revalida_el_centro_antes_de_cambiar_un_registro(
    caso_registro_medico,
):
    """Actualizar revalida el centro antes de cambiar un registro."""
    caso_registro_medico.repo.obtener_por_id.return_value = (
        caso_registro_medico.registro
    )
    caso_registro_medico.centro.en_servicio = False
    with pytest.raises(BusinessRuleError, match="no esta en servicio"):
        caso_registro_medico.servicio.actualizar_registro(
            caso_registro_medico.registro.id, caso_registro_medico.datos
        )
    caso_registro_medico.repo.actualizar.assert_not_called()
