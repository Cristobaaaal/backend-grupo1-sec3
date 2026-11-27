"""Reglas de asignación, transferencia, borrado y paginación de Pokémon."""

from datetime import date
from uuid import UUID

import pytest

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundException
from app.domain.models import (
    EstadoAtencion,
    Pokemon,
    RegistroMedico,
    TipoPokemon,
)

pytestmark = pytest.mark.unit


def test_crear_genera_id_y_conserva_los_datos_del_pokemon(caso_pokemon):
    """Crear genera id y conserva los datos del pokemon."""
    caso_pokemon.repo.save.side_effect = lambda pokemon: pokemon
    resultado = caso_pokemon.servicio.crear_pokemon(caso_pokemon.datos)
    assert isinstance(resultado.id, UUID)
    assert resultado.id.version == 4
    assert resultado.nombre == "Pikachu"
    assert resultado.tipo_principal == TipoPokemon.ELECTRICO
    assert (resultado.nivel, resultado.puntos_vida) == (10, 40)
    assert resultado.entrenador_id is None
    caso_pokemon.repo.save.assert_called_once_with(resultado)


def test_crear_rechaza_entrenador_inexistente_sin_guardar(caso_pokemon):
    """Crear rechaza entrenador inexistente sin guardar."""
    caso_pokemon.datos.entrenador_id = caso_pokemon.entrenador.id
    caso_pokemon.entrenadores.get_by_id.return_value = None
    with pytest.raises(NotFoundException) as error:
        caso_pokemon.servicio.crear_pokemon(caso_pokemon.datos)
    assert str(caso_pokemon.entrenador.id) in error.value.message
    caso_pokemon.repo.save.assert_not_called()


def test_asignar_guarda_el_entrenador_en_un_pokemon_libre(caso_pokemon):
    """Asignar guarda el entrenador en un pokemon libre."""
    esperado = Pokemon(
        caso_pokemon.pokemon.id,
        "Pikachu",
        TipoPokemon.ELECTRICO,
        10,
        40,
        caso_pokemon.entrenador.id,
    )
    caso_pokemon.repo.update.return_value = esperado
    resultado = caso_pokemon.servicio.asignar_entrenador(
        caso_pokemon.pokemon.id, caso_pokemon.entrenador.id
    )
    assert resultado == esperado
    pokemon_id, datos = caso_pokemon.repo.update.call_args.args
    assert pokemon_id == caso_pokemon.pokemon.id
    assert datos.entrenador_id == caso_pokemon.entrenador.id
    assert datos.nombre == "Pikachu"
    assert (datos.nivel, datos.puntos_vida) == (10, 40)
    caso_pokemon.repo.update.assert_called_once()


def test_asignar_rechaza_pokemon_que_ya_tiene_entrenador(caso_pokemon):
    """Asignar rechaza pokemon que ya tiene entrenador."""
    anterior = UUID(int=3)
    caso_pokemon.pokemon.entrenador_id = anterior
    with pytest.raises(BusinessRuleError, match="ya tiene un entrenador"):
        caso_pokemon.servicio.asignar_entrenador(
            caso_pokemon.pokemon.id, caso_pokemon.entrenador.id
        )
    assert caso_pokemon.pokemon.entrenador_id == anterior
    caso_pokemon.repo.update.assert_not_called()


def test_transferir_rechaza_al_mismo_entrenador_sin_escribir(caso_pokemon):
    """Transferir rechaza al mismo entrenador sin escribir."""
    caso_pokemon.pokemon.entrenador_id = caso_pokemon.entrenador.id
    with pytest.raises(BusinessRuleError, match="ya pertenece"):
        caso_pokemon.servicio.transferir_entrenador(
            caso_pokemon.pokemon.id, caso_pokemon.entrenador.id
        )
    assert caso_pokemon.pokemon.entrenador_id == caso_pokemon.entrenador.id
    caso_pokemon.repo.update.assert_not_called()


def test_buscar_pokemon_inexistente_devuelve_error_del_dominio(caso_pokemon):
    """Buscar pokemon inexistente devuelve error del dominio."""
    caso_pokemon.repo.get_by_id.return_value = None
    with pytest.raises(NotFoundException) as error:
        caso_pokemon.servicio.obtener_por_id(caso_pokemon.pokemon.id)
    assert error.value.code == "RESOURCE_NOT_FOUND"
    assert str(caso_pokemon.pokemon.id) in error.value.message


def test_eliminar_rechaza_pokemon_con_historial_medico(caso_pokemon):
    """Eliminar rechaza pokemon con historial medico."""
    caso_pokemon.registros.obtener_todos.return_value = [
        RegistroMedico(
            UUID(int=4),
            caso_pokemon.pokemon.id,
            UUID(int=5),
            "Agotamiento",
            date(2026, 1, 1),
            EstadoAtencion.DADO_DE_ALTA,
            5000,
        )
    ]
    with pytest.raises(ConflictError, match="registros médicos"):
        caso_pokemon.servicio.eliminar_pokemon(caso_pokemon.pokemon.id)
    caso_pokemon.repo.delete.assert_not_called()


def test_eliminar_permite_borrar_pokemon_sin_historial(caso_pokemon):
    """Eliminar permite borrar pokemon sin historial."""
    caso_pokemon.registros.obtener_todos.return_value = []
    caso_pokemon.repo.delete.return_value = True
    assert caso_pokemon.servicio.eliminar_pokemon(caso_pokemon.pokemon.id) is None
    caso_pokemon.repo.delete.assert_called_once_with(caso_pokemon.pokemon.id)


def test_paginacion_calcula_paginas_y_conserva_filtro_y_orden(caso_pokemon):
    """Paginacion calcula paginas y conserva filtro y orden."""
    caso_pokemon.repo.listar_paginado.return_value = ([caso_pokemon.pokemon], 5)
    resultado = caso_pokemon.servicio.listar_paginado(
        tipo=TipoPokemon.ELECTRICO,
        ordenar_por="nivel",
        direccion="desc",
        pagina=2,
        limite=2,
    )
    assert resultado.items == [caso_pokemon.pokemon]
    assert resultado.total == 5
    assert resultado.total_paginas == 3
    assert (resultado.pagina, resultado.limite) == (2, 2)
    caso_pokemon.repo.listar_paginado.assert_called_once_with(
        tipo=TipoPokemon.ELECTRICO,
        ordenar_por="nivel",
        direccion="desc",
        pagina=2,
        limite=2,
    )


@pytest.mark.parametrize(
    "parametros",
    [
        {"ordenar_por": "atributo_inexistente"},
        {"direccion": "otro"},
        {"pagina": 0},
        {"limite": 0},
        {"limite": 101},
    ],
    ids=[
        "columna-invalida",
        "direccion-invalida",
        "pagina-cero",
        "limite-cero",
        "limite-excesivo",
    ],
)
def test_paginacion_rechaza_parametros_invalidos_antes_de_consultar(
    caso_pokemon, parametros
):
    """Rechaza cada parámetro inválido sin llegar al repositorio."""
    with pytest.raises(BusinessRuleError):
        caso_pokemon.servicio.listar_paginado(**parametros)
    caso_pokemon.repo.listar_paginado.assert_not_called()
