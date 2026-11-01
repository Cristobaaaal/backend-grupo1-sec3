from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, Path, status
from app.schemas.schemas import CrearCentroPokemon, CentroPokemonResponse, ErrorResponse
from app.services.centro_pokemon_service import CentroPokemonService
from app.core.dependencies import get_centro_service

router = APIRouter(prefix="/centros-pokemon", tags=["Centros Pokemon"])
CentroId = Annotated[UUID, Path(description="ID del centro Pokémon", examples=["20000000-0000-4000-8000-000000000001"])]
Ciudad = Annotated[str, Path(description="Ciudad a consultar", examples=["Temuco"])]



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
def crear_centro(datos: CrearCentroPokemon, service: CentroPokemonService = Depends(get_centro_service)):
    return service.crear_centro(datos)


@router.get(
    "/",
    response_model=List[CentroPokemonResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar centros Pokémon",
    description="Devuelve todos los centros Pokémon registrados.",
)
def obtener_centros(service: CentroPokemonService = Depends(get_centro_service)):
    return service.obtener_todos()


@router.get(
    "/ciudad/{ciudad}",
    response_model=List[CentroPokemonResponse],
    status_code=status.HTTP_200_OK,
    summary="Buscar centros por ciudad",
    description="Devuelve los centros de la ciudad indicada. Si no hay coincidencias, devuelve una lista vacía.",
)
def obtener_centros_por_ciudad(ciudad: Ciudad, service: CentroPokemonService = Depends(get_centro_service)):
    return service.obtener_por_ciudad(ciudad)

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
def obtener_centro_por_id(centro_id: CentroId, service: CentroPokemonService = Depends(get_centro_service)):
    return service.obtener_por_id(centro_id)

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
def actualizar_centro_pokemon(centro_id: CentroId, datos: CrearCentroPokemon, service: CentroPokemonService = Depends(get_centro_service)):
    return service.actualizar_centro_pokemon(centro_id, datos)

@router.delete(
    "/{centro_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar centro Pokémon",
    description="Elimina un centro si no tiene pacientes en tratamiento ni registros médicos históricos.",
    responses={
        400: {"model": ErrorResponse, "description": "El centro tiene pacientes en tratamiento"},
        404: {"model": ErrorResponse, "description": "Centro no encontrado"},
        409: {"model": ErrorResponse, "description": "El centro tiene registros médicos históricos"},
        422: {"model": ErrorResponse, "description": "ID inválido"},
    },
)
def eliminar_centro_pokemon(centro_id: CentroId, service: CentroPokemonService = Depends(get_centro_service)):
    service.eliminar_centro_pokemon(centro_id)
