from typing import List
from uuid import UUID
from fastapi import APIRouter, status
from app.schemas.schemas import CrearCentroPokemon, CentroPokemonResponse, ErrorResponse
from app.services.centro_pokemon_service import CentroPokemonService
from app.core.dependencies import centro_pokemon_repo, registro_medico_repo

router = APIRouter(prefix="/centros-pokemon", tags=["Centros Pokemon"])

_service = CentroPokemonService(centro_pokemon_repo, registro_medico_repo)


@router.post(
    "/",
    response_model=CentroPokemonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear centro Pokémon",
    description="Registra un centro Pokémon y devuelve sus datos con el ID generado.",
    responses={
        422: {"model": ErrorResponse, "description": "Datos del centro inválidos"}
    },
)
def crear_centro(datos: CrearCentroPokemon):
    return _service.crear_centro(datos)


@router.get(
    "/",
    response_model=List[CentroPokemonResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar centros Pokémon",
    description="Devuelve todos los centros Pokémon registrados.",
)
def obtener_centros():
    return _service.obtener_todos()


@router.get(
    "/ciudad/{ciudad}",
    response_model=List[CentroPokemonResponse],
    status_code=status.HTTP_200_OK,
    summary="Buscar centros por ciudad",
    description="Devuelve los centros de la ciudad indicada. Si no hay coincidencias, devuelve una lista vacía.",
)
def obtener_centros_por_ciudad(ciudad: str):
    return _service.obtener_por_ciudad(ciudad)

@router.get(
    "/{centro_id}",
    response_model=CentroPokemonResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener centro Pokémon",
    description="Busca un centro Pokémon por su ID.",
    responses={
        404: {"model": ErrorResponse, "description": "Centro no encontrado"},
        422: {"model": ErrorResponse, "description": "ID inválido"},
    },
)
def obtener_centro_por_id(centro_id: UUID):
    return _service.obtener_por_id(centro_id)

@router.put(
    "/{centro_id}",
    response_model=CentroPokemonResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar centro Pokémon",
    description="Reemplaza los datos de un centro Pokémon existente.",
    responses={
        404: {"model": ErrorResponse, "description": "Centro no encontrado"},
        422: {"model": ErrorResponse, "description": "ID o datos inválidos"},
    },
)
def actualizar_centro_pokemon(centro_id: UUID, datos: CrearCentroPokemon):
    return _service.actualizar_centro_pokemon(centro_id, datos)

@router.delete(
    "/{centro_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar centro Pokémon",
    description="Elimina un centro si no tiene pacientes en tratamiento.",
    responses={
        400: {"model": ErrorResponse, "description": "El centro tiene pacientes en tratamiento"},
        404: {"model": ErrorResponse, "description": "Centro no encontrado"},
        422: {"model": ErrorResponse, "description": "ID inválido"},
    },
)
def eliminar_centro_pokemon(centro_id: UUID):
    _service.eliminar_centro_pokemon(centro_id)