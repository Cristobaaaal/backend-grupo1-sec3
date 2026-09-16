from fastapi import APIRouter, status
from typing import List
from uuid import UUID
from app.schemas.schemas import CrearEntrenador
from app.domain.models import Entrenador
from app.services.trainer_service import EntrenadorService
from app.repositories.trainer_repository import EntrenadorRepository

router = APIRouter(prefix="/entrenadores", tags=["Entrenadores"]) #todas las urls q tengan "entrenadores" van a tener la etiqueta de "Entrenadores"
_repo = EntrenadorRepository() #se instancia la clase EntrenadorRepository
_service = EntrenadorService(_repo) #se instancia la clase EntrenadorService

@router.post("/", response_model=Entrenador, status_code=status.HTTP_201_CREATED) #responde las peticiones para crear un entrenador
def crear_entrenador(datos: CrearEntrenador):
    return _service.crear_entrenador(datos)

@router.get("/", response_model=List[Entrenador], status_code=status.HTTP_200_OK) #responde las peticiones para buscar los entrenadores
def obtener_entrenadores():
    return _service.obtener_todos() #retorna todos los entrenadores

@router.get("/{entrenador_id}", response_model=Entrenador, status_code=status.HTTP_200_OK) #responde las peticiones para buscar por el id
def obtener_entrenador(entrenador_id: UUID):
    return _service.obtener_por_id(entrenador_id) #retorna el entrenador con el id

@router.put("/{entrenador_id}", response_model=Entrenador, status_code=status.HTTP_200_OK) #responde las peticiones para actualizar un entrenador
def actualizar_entrenador(entrenador_id: UUID, datos: CrearEntrenador):
    return _service.actualizar_entrenador(entrenador_id, datos) #retorna el entrenador actualizado

@router.delete("/{entrenador_id}", status_code=status.HTTP_204_NO_CONTENT) #responde las peticiones para eliminar un entrenador
def eliminar_entrenador(entrenador_id: UUID):
    _service.eliminar_entrenador(entrenador_id) #elimina el entrenador con el id