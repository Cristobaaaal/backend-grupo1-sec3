from typing import List
from uuid import UUID
from fastapi import APIRouter, status
from app.domain.models import CentroPokemon
from app.schemas.schemas import CrearCentroPokemon
from app.services.centro_pokemon_service import CentroPokemonService
from app.core.dependencies import centro_pokemon_repo, registro_medico_repo

router = APIRouter(prefix="/centros-pokemon", tags=["Centros Pokemon"])

_service = CentroPokemonService(_repo)


@router.post("/", response_model=CentroPokemon, status_code=status.HTTP_201_CREATED)
def crear_centro(datos: CrearCentroPokemon):
    return _service.crear_centro(datos)


@router.get("/", response_model=List[CentroPokemon], status_code=status.HTTP_200_OK)
def obtener_centros():
    return _service.obtener_todos()


@router.get("/ciudad/{ciudad}", response_model=List[CentroPokemon], status_code=status.HTTP_200_OK)
def obtener_centros_por_ciudad(ciudad: str):
    return _service.obtener_por_ciudad(ciudad)

@router.get("/{centro_id}", response_model=CentroPokemon, status_code=status.HTTP_200_OK)
def obtener_centro_por_id(centro_id: UUID):
    return _service.obtener_por_id(centro_id)

@router.put("/{centro_id}", response_model=CentroPokemon, status_code=status.HTTP_200_OK)
def actualizar_centro_pokemon(centro_id: UUID, datos: CrearCentroPokemon):
    return _service.actualizar_centro_pokemon(centro_id, datos)

@router.delete("/{centro_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_centro_pokemon(centro_id: UUID):
    _service.eliminar_centro_pokemon(centro_id)