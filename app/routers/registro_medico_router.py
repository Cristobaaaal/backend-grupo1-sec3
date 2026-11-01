from fastapi import APIRouter, Depends, Path, status
from uuid import UUID
from typing import Annotated, List
from app.schemas.schemas import CrearRegistroMedico, ErrorResponse, RegistroMedicoResponse
from app.services.registro_medico_service import RegistroMedicoService
from app.core.dependencies import get_registro_service

router = APIRouter(
    prefix="/registros-medicos",
    tags=["registros medicos"]
)
ERROR_422 = {422: {"model": ErrorResponse, "description": "ID o datos inválidos"}}
RegistroId = Annotated[UUID, Path(description="ID del registro médico", examples=["40000000-0000-4000-8000-000000000001"])]


@router.post(
    "/", response_model=RegistroMedicoResponse, status_code=status.HTTP_201_CREATED,
    summary="Crear registro médico",
    description="Registra la atención de un Pokémon en un centro en servicio. La fecha no puede ser futura.",
    responses={**ERROR_422,
               400: {"model": ErrorResponse, "description": "Centro fuera de servicio o fecha futura"},
               404: {"model": ErrorResponse, "description": "Pokémon o centro no encontrado"},
               409: {"model": ErrorResponse, "description": "Conflicto al guardar las referencias"}},
)
def crear_registro(datos: CrearRegistroMedico, service: RegistroMedicoService = Depends(get_registro_service)):
    return service.crear_registro(datos)

@router.get(
    "/{registro_id}", response_model=RegistroMedicoResponse,
    summary="Obtener registro médico", description="Busca un registro médico por su ID.",
    responses={**ERROR_422, 404: {"model": ErrorResponse, "description": "Registro no encontrado"}},
)
def obtener_registro(registro_id: RegistroId, service: RegistroMedicoService = Depends(get_registro_service)):
    return service.obtener_por_id(registro_id)

@router.get(
    "/", response_model=List[RegistroMedicoResponse],
    summary="Listar registros médicos",
    description="Devuelve todos los registros médicos guardados. Una lista vacía indica que aún no hay registros.",
)
def listar_registros(service: RegistroMedicoService = Depends(get_registro_service)):
    return service.listar_registros()

@router.put(
    "/{registro_id}", response_model=RegistroMedicoResponse,
    summary="Actualizar registro médico",
    description="Reemplaza los datos de un registro existente. El Pokémon y el centro deben existir; el centro debe estar en servicio y la fecha no puede ser futura.",
    responses={**ERROR_422,
               400: {"model": ErrorResponse, "description": "Centro fuera de servicio o fecha futura"},
               404: {"model": ErrorResponse, "description": "Registro, Pokémon o centro no encontrado"},
               409: {"model": ErrorResponse, "description": "Conflicto al guardar las referencias"}},
)
def actualizar_registro(registro_id: RegistroId, datos: CrearRegistroMedico, service: RegistroMedicoService = Depends(get_registro_service)):
    return service.actualizar_registro(registro_id, datos)

@router.delete(
    "/{registro_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar registro médico", description="Elimina un registro médico por su ID.",
    responses={**ERROR_422, 404: {"model": ErrorResponse, "description": "Registro no encontrado"}},
)
def eliminar_registro(registro_id: RegistroId, service: RegistroMedicoService = Depends(get_registro_service)):
    service.eliminar_registro(registro_id)
