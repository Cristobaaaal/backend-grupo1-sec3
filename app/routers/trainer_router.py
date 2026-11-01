from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, Path, status

from app.core.dependencies import get_trainer_service
from app.schemas.schemas import CrearEntrenador, EntrenadorResponse, ErrorResponse
from app.services.trainer_service import EntrenadorService


router = APIRouter(prefix="/entrenadores", tags=["Entrenadores"])
EntrenadorId = Annotated[UUID, Path(description="ID del entrenador", examples=["10000000-0000-4000-8000-000000000001"])]


@router.post(
    "/",
    response_model=EntrenadorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear entrenador",
    description="Registra un entrenador y devuelve sus datos con el ID generado.",
    responses={
        422: {"model": ErrorResponse, "description": "Datos del entrenador inválidos"}
    },
)
def crear_entrenador(
    datos: CrearEntrenador,
    service: EntrenadorService = Depends(get_trainer_service),
):
    return service.crear_entrenador(datos)


@router.get(
    "/",
    response_model=List[EntrenadorResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar entrenadores",
    description="Devuelve todos los entrenadores registrados.",
)
def obtener_entrenadores(
    service: EntrenadorService = Depends(get_trainer_service),
):
    return service.obtener_todos()


@router.get(
    "/{entrenador_id}",
    response_model=EntrenadorResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener entrenador",
    description="Busca un entrenador por su ID. Devuelve 404 si no existe.",
    responses={
        404: {"model": ErrorResponse, "description": "Entrenador no encontrado"},
        422: {"model": ErrorResponse, "description": "ID inválido"},
    },
)
def obtener_entrenador(
    entrenador_id: EntrenadorId,
    service: EntrenadorService = Depends(get_trainer_service),
):
    return service.obtener_por_id(entrenador_id)


@router.put(
    "/{entrenador_id}",
    response_model=EntrenadorResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar entrenador",
    description="Reemplaza los datos de un entrenador existente. Devuelve 404 si no existe.",
    responses={
        404: {"model": ErrorResponse, "description": "Entrenador no encontrado"},
        422: {"model": ErrorResponse, "description": "ID o datos inválidos"},
    },
)
def actualizar_entrenador(
    entrenador_id: EntrenadorId,
    datos: CrearEntrenador,
    service: EntrenadorService = Depends(get_trainer_service),
):
    return service.actualizar_entrenador(entrenador_id, datos)


@router.delete(
    "/{entrenador_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar entrenador",
    description="Elimina un entrenador si no tiene Pokémon asignados.",
    responses={
        404: {"model": ErrorResponse, "description": "Entrenador no encontrado"},
        409: {"model": ErrorResponse, "description": "El entrenador tiene Pokémon asignados"},
        422: {"model": ErrorResponse, "description": "ID inválido"},
    },
)
def eliminar_entrenador(
    entrenador_id: EntrenadorId,
    service: EntrenadorService = Depends(get_trainer_service),
):
    service.eliminar_entrenador(entrenador_id)
