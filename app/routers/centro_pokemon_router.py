from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, status

from app.core.dependencies import get_centro_service, get_current_user
from app.domain.models import RolUsuario
from app.schemas.schemas import (
    CentroPokemonResponse,
    CrearCentroPokemon,
    ErrorResponse,
)
from app.security.permissions import require_roles
from app.services.centro_pokemon_service import CentroPokemonService

router = APIRouter(
    prefix="/centros-pokemon",
    tags=["Centros Pokemon"],
    dependencies=[Depends(get_current_user)],
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Token inválido, vencido o ausente.",
        },
    },
)

CentroId = Annotated[
    UUID,
    Path(
        description="ID del centro Pokémon",
        examples=["20000000-0000-4000-8000-000000000001"],
    ),
]

Ciudad = Annotated[
    str,
    Path(
        description="Ciudad a consultar",
        examples=["Temuco"],
    ),
]


@router.post(
    "/",
    response_model=CentroPokemonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear centro Pokémon",
    description=("Registra un centro Pokémon. Requiere rol ADMIN o VETERINARIO."),
    dependencies=[Depends(require_roles(RolUsuario.ADMIN, RolUsuario.VETERINARIO))],
    responses={
        403: {
            "model": ErrorResponse,
            "description": "El rol no permite crear centros.",
        },
        422: {
            "model": ErrorResponse,
            "description": "Datos del centro inválidos.",
        },
    },
)
def crear_centro(
    datos: CrearCentroPokemon,
    service: CentroPokemonService = Depends(get_centro_service),
):
    return service.crear_centro(datos)


@router.get(
    "/",
    response_model=list[CentroPokemonResponse],
    summary="Listar centros Pokémon",
    description=(
        "Devuelve todos los centros registrados. Requiere un usuario autenticado."
    ),
)
def obtener_centros(
    service: CentroPokemonService = Depends(get_centro_service),
):
    return service.obtener_todos()


@router.get(
    "/ciudad/{ciudad}",
    response_model=list[CentroPokemonResponse],
    summary="Buscar centros por ciudad",
    description=(
        "Devuelve los centros de la ciudad indicada. "
        "Si no hay coincidencias, devuelve una lista vacía. "
        "Requiere un usuario autenticado."
    ),
)
def obtener_centros_por_ciudad(
    ciudad: Ciudad,
    service: CentroPokemonService = Depends(get_centro_service),
):
    return service.obtener_por_ciudad(ciudad)


@router.get(
    "/{centro_id}",
    response_model=CentroPokemonResponse,
    summary="Obtener centro Pokémon",
    description=("Busca un centro por su ID. Requiere un usuario autenticado."),
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Centro no encontrado.",
        },
        422: {
            "model": ErrorResponse,
            "description": "ID inválido.",
        },
    },
)
def obtener_centro_por_id(
    centro_id: CentroId,
    service: CentroPokemonService = Depends(get_centro_service),
):
    return service.obtener_por_id(centro_id)


@router.put(
    "/{centro_id}",
    response_model=CentroPokemonResponse,
    summary="Actualizar centro Pokémon",
    description=(
        "Reemplaza los datos de un centro existente. Requiere rol ADMIN o VETERINARIO."
    ),
    dependencies=[Depends(require_roles(RolUsuario.ADMIN, RolUsuario.VETERINARIO))],
    responses={
        403: {
            "model": ErrorResponse,
            "description": "El rol no permite actualizar centros.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Centro no encontrado.",
        },
        422: {
            "model": ErrorResponse,
            "description": "ID o datos inválidos.",
        },
    },
)
def actualizar_centro_pokemon(
    centro_id: CentroId,
    datos: CrearCentroPokemon,
    service: CentroPokemonService = Depends(get_centro_service),
):
    return service.actualizar_centro_pokemon(centro_id, datos)


@router.delete(
    "/{centro_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar centro Pokémon",
    description=(
        "Operación exclusiva del rol ADMIN. "
        "Elimina un centro si no tiene pacientes en tratamiento "
        "ni registros médicos históricos."
    ),
    dependencies=[Depends(require_roles(RolUsuario.ADMIN))],
    responses={
        400: {
            "model": ErrorResponse,
            "description": "El centro tiene pacientes en tratamiento.",
        },
        403: {
            "model": ErrorResponse,
            "description": "Solo ADMIN puede eliminar centros.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Centro no encontrado.",
        },
        409: {
            "model": ErrorResponse,
            "description": "El centro tiene registros médicos históricos.",
        },
        422: {
            "model": ErrorResponse,
            "description": "ID inválido.",
        },
    },
)
def eliminar_centro_pokemon(
    centro_id: CentroId,
    service: CentroPokemonService = Depends(get_centro_service),
):
    service.eliminar_centro_pokemon(centro_id)
