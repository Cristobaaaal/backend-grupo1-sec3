"""Persistencia, restricciones y recuperación de la sesión con PostgreSQL real."""

from dataclasses import replace
from datetime import date
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.domain.models import Pokemon, TipoPokemon
from app.repositories.trainer_repository import EntrenadorRepository
from app.schemas.schemas import CrearPokemon, CrearRegistroMedico
from tests.database import PROJECT_ROOT

pytestmark = pytest.mark.integration


def test_migraciones_crean_el_esquema_completo_y_llegan_a_head(migrated_database):
    """Comprueba las tablas reales y la revisión aplicada, sin create_all."""
    tables = set(inspect(migrated_database).get_table_names())
    assert {
        "entrenadores",
        "pokemones",
        "centros_pokemon",
        "registros_medicos",
        "usuarios",
        "refresh_tokens",
        "password_reset_tokens",
        "alembic_version",
        "auth_sessions",
        "auth_rate_limits",
    } <= tables
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    with migrated_database.connect() as connection:
        applied = MigrationContext.configure(connection).get_current_heads()

    assert set(applied) == set(ScriptDirectory.from_config(config).get_heads())


def test_entrenador_persiste_al_cerrar_y_abrir_otra_sesion(
    clean_database, crear_entrenador
):
    """Una sesión independiente puede leer los datos confirmados por el repo."""
    entrenador = crear_entrenador()

    with Session(clean_database) as nueva_sesion:
        resultado = EntrenadorRepository(nueva_sesion).get_by_id(entrenador.id)

    assert resultado == entrenador
    assert isinstance(resultado.id, UUID)


def test_id_duplicado_hace_rollback_y_la_sesion_sigue_operativa(
    repositorios, crear_entrenador
):
    """Rechaza una PK repetida, conserva el original y permite otra escritura."""
    original = crear_entrenador()

    with pytest.raises(ConflictError):
        repositorios.entrenadores.save(replace(original, nombre="Misty"))

    assert repositorios.entrenadores.get_by_id(original.id) == original
    segundo = crear_entrenador("Brock")
    assert {e.id for e in repositorios.entrenadores.get_all()} == {
        original.id,
        segundo.id,
    }


def test_fk_de_pokemon_rechaza_entrenador_inexistente_sin_dejar_datos(
    repositorios, crear_pokemon
):
    """La BD rechaza la relación inexistente y el repo recupera su sesión."""
    invalido = Pokemon(uuid4(), "Pikachu", TipoPokemon.ELECTRICO, 10, 40, uuid4())

    with pytest.raises(ConflictError):
        repositorios.pokemones.save(invalido)

    assert repositorios.pokemones.get_all() == []
    valido = crear_pokemon()
    assert repositorios.pokemones.get_by_id(valido.id) == valido


def test_bd_impide_borrar_entrenador_con_pokemon_y_conserva_la_relacion(
    repositorios, crear_entrenador, crear_pokemon
):
    """La FK protege la relación incluso al usar directamente el repositorio."""
    entrenador = crear_entrenador()
    pokemon = crear_pokemon(entrenador_id=entrenador.id)

    with pytest.raises(ConflictError):
        repositorios.entrenadores.delete(entrenador.id)

    assert repositorios.entrenadores.get_by_id(entrenador.id) == entrenador
    assert repositorios.pokemones.get_by_id(pokemon.id).entrenador_id == entrenador.id


def test_actualizacion_con_fk_invalida_revierte_todos_los_cambios(
    db_session, repositorios, crear_entrenador, crear_pokemon
):
    """Un UPDATE fallido conserva entrenador, nombre y nivel anteriores."""
    entrenador = crear_entrenador()
    pokemon = crear_pokemon(entrenador_id=entrenador.id)
    nuevos_datos = CrearPokemon(
        nombre="Raichu",
        tipo_principal="ELECTRICO",
        nivel=35,
        puntos_vida=80,
        entrenador_id=uuid4(),
    )

    with pytest.raises(ConflictError):
        repositorios.pokemones.update(pokemon.id, nuevos_datos)

    db_session.expire_all()
    assert repositorios.pokemones.get_by_id(pokemon.id) == pokemon


def test_registro_rechaza_centro_inexistente_y_admite_uno_valido_despues(
    repositorios, crear_pokemon, crear_centro
):
    """Comprueba FK y rollback al crear un registro médico con centro inválido."""
    pokemon = crear_pokemon()
    datos = CrearRegistroMedico(
        pokemon_id=pokemon.id,
        centro_id=uuid4(),
        diagnostico="Agotamiento",
        fecha_ingreso=date(2026, 1, 1),
        estado="EN_TRATAMIENTO",
        costo=5000,
    )

    with pytest.raises(ConflictError):
        repositorios.registros.guardar(datos)

    assert repositorios.registros.obtener_todos() == []
    centro = crear_centro()
    registro = repositorios.registros.guardar(
        datos.model_copy(update={"centro_id": centro.id})
    )
    assert registro.pokemon_id == pokemon.id
    assert registro.centro_id == centro.id
    assert repositorios.registros.obtener_por_id(registro.id) == registro


@pytest.mark.parametrize("recurso", ["pokemon", "centro"], ids=["pokemon", "centro"])
def test_bd_impide_borrar_entidades_con_historial_medico(
    repositorios, historial_medico, recurso
):
    """Las FK preservan el historial aunque el paciente ya tenga el alta."""
    if recurso == "pokemon":
        repositorio = repositorios.pokemones
        entidad = historial_medico.pokemon
    else:
        repositorio = repositorios.centros
        entidad = historial_medico.centro

    with pytest.raises(ConflictError):
        repositorio.delete(entidad.id)

    assert repositorio.get_by_id(entidad.id) == entidad
    assert (
        repositorios.registros.obtener_por_id(historial_medico.registro.id)
        == historial_medico.registro
    )


def test_paginacion_desempata_por_id_y_no_repite_filas_entre_paginas(
    repositorios, crear_pokemon
):
    """Ordena por nivel e ID; el filtro excluye tipos ajenos al conteo."""
    primero = crear_pokemon(nombre="Pikachu", pokemon_id=UUID(int=1))
    segundo = crear_pokemon(nombre="Raichu", pokemon_id=UUID(int=2))
    crear_pokemon(nombre="Charmander", tipo=TipoPokemon.FUEGO)

    pagina_uno, total = repositorios.pokemones.listar_paginado(
        tipo=TipoPokemon.ELECTRICO,
        ordenar_por="nivel",
        pagina=1,
        limite=1,
    )
    pagina_dos, segundo_total = repositorios.pokemones.listar_paginado(
        tipo=TipoPokemon.ELECTRICO,
        ordenar_por="nivel",
        pagina=2,
        limite=1,
    )

    assert [p.id for p in pagina_uno] == [primero.id]
    assert [p.id for p in pagina_dos] == [segundo.id]
    assert total == segundo_total == 2


def test_busqueda_de_centro_ignora_mayusculas_sin_incluir_otras_ciudades(
    repositorios, crear_centro
):
    """La comparación de ciudad es exacta e insensible a mayúsculas."""
    esperado = crear_centro("Temuco")
    crear_centro("Temuco Sur")

    encontrados = repositorios.centros.get_by_ciudad("tEmUcO")

    assert [centro.id for centro in encontrados] == [esperado.id]
