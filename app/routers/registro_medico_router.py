from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from typing import List
from app.schemas.schemas import CrearRegistroMedico
from app.domain.models import RegistroMedico
from app.services.registro_medico_service import RegistroMedicoService
from app.repositories.registro_medico_repository import RegistroMedicoRepository

router = APIRouter(
    prefix="/registros-medicos",
    tags=["Registros Médicos"]
)


repository = RegistroMedicoRepository()
service = RegistroMedicoService(repository)

@router.post("/", response_model=RegistroMedico, status_code=status.HTTP_201_CREATED)
def crear_registro(datos: CrearRegistroMedico):
    return service.crear_registro(datos)

@router.get("/{registro_id}", response_model=RegistroMedico)
def obtener_registro(registro_id: UUID):
    registro = service.obtener_por_id(registro_id)

    if not registro:
        raise HTTPException(status_code=404, detail="Registro médico no encontrado")
    return registro

@router.get("/", response_model=List[RegistroMedico])
def listar_registros():
    return service.listar_registros()

@router.put("/{registro_id}", response_model=RegistroMedico)
def actualizar_registro(registro_id: UUID, datos: CrearRegistroMedico):
    registro_actualizado = service.actualizar_registro(registro_id, datos)

    if not registro_actualizado:
        raise HTTPException(status_code=404, detail="Registro médico no encontrado")
    return registro_actualizado

@router.delete("/{registro_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_registro(registro_id: UUID):
    eliminado = service.eliminar_registro(registro_id)

    if not eliminado:
        raise HTTPException(status_code=404, detail="Registro médico no encontrado")
    return None