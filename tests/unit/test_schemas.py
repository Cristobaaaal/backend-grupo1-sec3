"""Validaciones de entrada, siguiendo los casos de schemas de Student."""

from uuid import UUID

import pytest
from pydantic import ValidationError

from app.domain.models import TipoPokemon
from app.schemas.schemas import CrearCentroPokemon, CrearEntrenador, CrearPokemon

pytestmark = pytest.mark.unit


def test_crear_pokemon_valido_sin_entrenador(pokemon_payload):
    """Acepta un Pokémon válido y deja libre la relación opcional."""
    datos = CrearPokemon(**pokemon_payload())

    assert datos.nombre == "Pikachu"
    assert datos.tipo_principal == TipoPokemon.ELECTRICO
    assert (datos.nivel, datos.puntos_vida) == (10, 40)
    assert datos.entrenador_id is None


def test_crear_pokemon_convierte_el_id_de_entrenador(pokemon_payload):
    """Convierte el UUID del payload al tipo usado por el dominio."""
    entrenador_id = UUID(int=1)

    datos = CrearPokemon(**pokemon_payload(entrenador_id=str(entrenador_id)))

    assert datos.entrenador_id == entrenador_id


@pytest.mark.parametrize(
    ("campo", "valor", "tipo_error"),
    [
        ("nombre", "", "string_too_short"),
        ("nombre", "a" * 16, "string_too_long"),
        ("tipo_principal", "DESCONOCIDO", "enum"),
        ("nivel", 0, "greater_than_equal"),
        ("nivel", 101, "less_than_equal"),
        ("puntos_vida", 0, "greater_than_equal"),
        ("puntos_vida", 101, "less_than_equal"),
        ("entrenador_id", "no-es-un-uuid", "uuid_parsing"),
    ],
    ids=[
        "nombre-vacio",
        "nombre-largo",
        "tipo-desconocido",
        "nivel-bajo",
        "nivel-alto",
        "vida-baja",
        "vida-alta",
        "entrenador-uuid-invalido",
    ],
)
def test_crear_pokemon_rechaza_campo_invalido(
    pokemon_payload, campo, valor, tipo_error
):
    """Rechaza el valor e identifica el campo y la regla que fallaron."""
    with pytest.raises(ValidationError) as error:
        CrearPokemon(**pokemon_payload(**{campo: valor}))

    assert [(e["loc"], e["type"]) for e in error.value.errors()] == [
        ((campo,), tipo_error)
    ]


@pytest.mark.parametrize("medallas", [0, 8], ids=["sin-medallas", "ocho-medallas"])
def test_entrenador_acepta_los_limites_de_medallas(medallas):
    """Admite los dos extremos válidos de la cantidad de medallas."""
    datos = CrearEntrenador(
        nombre="Ash",
        nivel_experiencia=10,
        region_origen="Kanto",
        medallas_obtenidas=medallas,
    )

    assert datos.medallas_obtenidas == medallas


@pytest.mark.parametrize("medallas", [-1, 9], ids=["medallas-negativas", "mas-de-ocho"])
def test_entrenador_rechaza_medallas_fuera_de_rango(medallas):
    """Rechaza cantidades inferiores a cero o superiores a ocho."""
    with pytest.raises(ValidationError) as error:
        CrearEntrenador(
            nombre="Ash",
            nivel_experiencia=10,
            region_origen="Kanto",
            medallas_obtenidas=medallas,
        )

    assert error.value.errors()[0]["loc"] == ("medallas_obtenidas",)


@pytest.mark.parametrize(
    "capacidad", [0, 101], ids=["sin-capacidad", "capacidad-excesiva"]
)
def test_centro_rechaza_capacidad_fuera_de_rango(capacidad):
    """Impide registrar un centro con capacidad fuera de 1 a 100."""
    with pytest.raises(ValidationError) as error:
        CrearCentroPokemon(
            nombre="Centro Norte",
            ciudad="Temuco",
            capacidad_maxima=capacidad,
        )

    assert error.value.errors()[0]["loc"] == ("capacidad_maxima",)
