from fastapi import APIRouter, status
from uuid import UUID
from typing import List
from app.schemas.schemas import CrearRegistroMedico
from app.domain.models import RegistroMedico
from app.services.registro_medico_service import RegistroMedicoService
from app.core.dependencies import registro_medico_repo, pokemon_repo, centro_pokemon_repo

router = APIRouter(
    prefix="/registros-medicos",
    tags=["registros medicos"]
)

service = RegistroMedicoService(registro_medico_repo, pokemon_repo, centro_pokemon_repo)

@router.post("/", response_model=RegistroMedico, status_code=status.HTTP_201_CREATED)
def crear_registro(datos: CrearRegistroMedico):
    return service.crear_registro(datos)

@router.get("/{registro_id}", response_model=RegistroMedico)
def obtener_registro(registro_id: UUID):
    return service.obtener_por_id(registro_id)

@router.get("/", response_model=List[RegistroMedico])
def listar_registros():
    return service.listar_registros()

@router.put("/{registro_id}", response_model=RegistroMedico)
def actualizar_registro(registro_id: UUID, datos: CrearRegistroMedico):
    return service.actualizar_registro(registro_id, datos)

@router.delete("/{registro_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_registro(registro_id: UUID):
    service.eliminar_registro(registro_id)