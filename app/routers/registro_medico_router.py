from fastapi import APIRouter, Depends, status
from uuid import UUID
from typing import List
from app.schemas.schemas import CrearRegistroMedico, RegistroMedicoResponse
from app.services.registro_medico_service import RegistroMedicoService
from app.core.dependencies import get_registro_service

router = APIRouter(
    prefix="/registros-medicos",
    tags=["registros medicos"]
)


@router.post("/", response_model=RegistroMedicoResponse, status_code=status.HTTP_201_CREATED)
def crear_registro(datos: CrearRegistroMedico, service: RegistroMedicoService = Depends(get_registro_service)):
    return service.crear_registro(datos)

@router.get("/{registro_id}", response_model=RegistroMedicoResponse)
def obtener_registro(registro_id: UUID, service: RegistroMedicoService = Depends(get_registro_service)):
    return service.obtener_por_id(registro_id)

@router.get("/", response_model=List[RegistroMedicoResponse])
def listar_registros(service: RegistroMedicoService = Depends(get_registro_service)):
    return service.listar_registros()

@router.put("/{registro_id}", response_model=RegistroMedicoResponse)
def actualizar_registro(registro_id: UUID, datos: CrearRegistroMedico, service: RegistroMedicoService = Depends(get_registro_service)):
    return service.actualizar_registro(registro_id, datos)

@router.delete("/{registro_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_registro(registro_id: UUID, service: RegistroMedicoService = Depends(get_registro_service)):
    service.eliminar_registro(registro_id)
