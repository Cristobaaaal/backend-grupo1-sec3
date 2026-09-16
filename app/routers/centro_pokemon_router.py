from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from app.domain.models import CentroPokemon
from app.repositories.centro_pokemon_repository import CentroPokemonRepository
from app.schemas.schemas import CrearCentroPokemon
from app.services.centro_pokemon_service import CentroPokemonService

router = APIRouter(prefix="/centros-pokemon", tags=["Centros Pokemon"])

_repo = CentroPokemonRepository()
_service = CentroPokemonService(_repo)


@router.post("/", response_model=CentroPokemon, status_code=status.HTTP_201_CREATED)
def crear_centro(datos: CrearCentroPokemon):
    try:
        return _service.crear_centro(datos)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/", response_model=List[CentroPokemon], status_code=status.HTTP_200_OK)
def obtener_centros():
    return _service.obtener_todos()


@router.get("/ciudad/{ciudad}", response_model=List[CentroPokemon], status_code=status.HTTP_200_OK)
def obtener_centros_por_ciudad(ciudad: str):
    return _service.obtener_por_ciudad(ciudad)


@router.get("/{centro_id}", response_model=CentroPokemon, status_code=status.HTTP_200_OK)
def obtener_centro_por_id(centro_id: UUID):
    try:
        return _service.obtener_por_id(centro_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )