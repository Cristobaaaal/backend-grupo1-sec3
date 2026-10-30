from fastapi import APIRouter, status
from typing import List
from uuid import UUID
from app.schemas.schemas import CrearEntrenador, EntrenadorResponse, ErrorResponse
from app.services.trainer_service import EntrenadorService
from app.core.dependencies import trainer_repo

router = APIRouter(prefix="/entrenadores", tags=["Entrenadores"]) #todas las urls q tengan "entrenadores" van a tener la etiqueta de "Entrenadores"
_service = EntrenadorService(trainer_repo) #se instancia la clase EntrenadorService

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
def crear_entrenador(datos: CrearEntrenador):
    return _service.crear_entrenador(datos)

@router.get(
    "/",
    response_model=List[EntrenadorResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar entrenadores",
    description="Devuelve todos los entrenadores registrados.",
)
def obtener_entrenadores():
    return _service.obtener_todos()

@router.get(
    "/{entrenador_id}",
    response_model=EntrenadorResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener entrenador",
    description="Busca un entrenador por su ID. Devuelve 404 si no existe.",
    responses={
        404: {"model": ErrorResponse, "description": "Entrenador no encontrado"}
    },
)
def obtener_entrenador(entrenador_id: UUID):
    return _service.obtener_por_id(entrenador_id)#retorna el entrenador con el id

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
def actualizar_entrenador(entrenador_id: UUID, datos: CrearEntrenador):
    return _service.actualizar_entrenador(entrenador_id, datos) #retorna el entrenador actualizado

@router.delete(
    "/{entrenador_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar entrenador",
    description="Elimina un entrenador por su ID. Devuelve 404 si no existe.",
    responses={
        404: {"model": ErrorResponse, "description": "Entrenador no encontrado"},
        422: {"model": ErrorResponse, "description": "ID inválido"},
    },
)
def eliminar_entrenador(entrenador_id: UUID):
    _service.eliminar_entrenador(entrenador_id)