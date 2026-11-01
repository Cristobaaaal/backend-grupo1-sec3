from fastapi import APIRouter, Depends, Path, status, Query
from typing import Annotated, List, Optional
from uuid import UUID
from app.schemas.schemas import CrearPokemon, ErrorResponse, PaginatedResponse, PokemonResponse
from app.domain.models import TipoPokemon
from app.services.pokemon_service import PokemonService 
from app.core.dependencies import get_pokemon_service

router = APIRouter(prefix="/pokemones", tags=["Pokemones"]) #todas las urls q tengan "pokemones" van a tener la etiqueta de "Pokemones"
ERROR_422 = {422: {"model": ErrorResponse, "description": "Parámetros o datos inválidos"}}
PokemonId = Annotated[UUID, Path(description="ID del Pokémon", examples=["30000000-0000-4000-8000-000000000001"])]
EntrenadorId = Annotated[UUID, Path(description="ID del entrenador", examples=["10000000-0000-4000-8000-000000000001"])]
Tipo = Annotated[TipoPokemon, Path(description="Tipo principal", examples=["ELECTRICO"])]

@router.post(
    "/", response_model=PokemonResponse, status_code=status.HTTP_201_CREATED,
    summary="Crear Pokémon",
    description="Registra un Pokémon. Si se indica entrenador_id, el entrenador debe existir.",
    responses={**ERROR_422,
               404: {"model": ErrorResponse, "description": "Entrenador no encontrado"},
               409: {"model": ErrorResponse, "description": "Conflicto al guardar el Pokémon"}},
)
def crear_pokemon(datos: CrearPokemon, service: PokemonService = Depends(get_pokemon_service)):
    return service.crear_pokemon(datos)

@router.get(
    "/", response_model=PaginatedResponse[PokemonResponse], status_code=status.HTTP_200_OK,
    summary="Listar Pokémon con filtro, orden y paginación",
    description="Filtra por tipo, ordena por nombre, nivel o puntos de vida y devuelve una página. El total corresponde a los registros filtrados.",
    responses={**ERROR_422,
               400: {"model": ErrorResponse, "description": "Campo o dirección de ordenamiento inválidos"}},
)
def obtener_pokemones(
    tipo: Optional[TipoPokemon] = Query(None, description="Tipo principal; omitir para incluir todos", examples=["ELECTRICO"]),
    ordenar_por: str = Query("nombre", description="nombre | nivel | puntos_vida", examples=["nivel"]),
    direccion: str = Query("asc", description="asc o desc", examples=["desc"]),
    pagina: int = Query(1, ge=1, examples=[1]),
    limite: int = Query(20, ge=1, le=100, examples=[20]),
    service: PokemonService = Depends(get_pokemon_service),
):
    return service.listar_paginado(
        tipo=tipo, ordenar_por=ordenar_por, direccion=direccion, pagina=pagina, limite=limite
    )

@router.get(
    "/sin-entrenador", response_model=List[PokemonResponse], status_code=status.HTTP_200_OK,
    summary="Listar Pokémon sin entrenador",
    description="Devuelve los Pokémon sin entrenador. Una lista vacía indica que no hay coincidencias.",
)
def obtener_sin_entrenador(service: PokemonService = Depends(get_pokemon_service)):
    return service.obtener_sin_entrenador()

@router.get(
    "/tipo/{tipo}", response_model=List[PokemonResponse], status_code=status.HTTP_200_OK,
    summary="Buscar Pokémon por tipo",
    description="Devuelve los Pokémon del tipo indicado. Una lista vacía indica que no hay coincidencias.",
    responses=ERROR_422,
)
def obtener_por_tipo(tipo: Tipo, service: PokemonService = Depends(get_pokemon_service)):
    return service.obtener_por_tipo(tipo)

@router.get(
    "/{pokemon_id}", response_model=PokemonResponse, status_code=status.HTTP_200_OK,
    summary="Obtener Pokémon", description="Busca un Pokémon por su ID.",
    responses={**ERROR_422, 404: {"model": ErrorResponse, "description": "Pokémon no encontrado"}},
)
def obtener_pokemon(pokemon_id: PokemonId, service: PokemonService = Depends(get_pokemon_service)):
    return service.obtener_por_id(pokemon_id) #retorna el pokemon con el id

@router.get(
    "/entrenador/{entrenador_id}", response_model=List[PokemonResponse], status_code=status.HTTP_200_OK,
    summary="Listar Pokémon de un entrenador",
    description="Devuelve los Pokémon asociados al ID de entrenador. Una lista vacía indica que no hay coincidencias.",
    responses=ERROR_422,
)
def obtener_pokemones_por_entrenador(entrenador_id: EntrenadorId, service: PokemonService = Depends(get_pokemon_service)):
    return service.obtener_por_entrenador(entrenador_id)

@router.delete(
    "/{pokemon_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar Pokémon", description="Elimina un Pokémon si no tiene registros médicos asociados.",
    responses={**ERROR_422,
               404: {"model": ErrorResponse, "description": "Pokémon no encontrado"},
               409: {"model": ErrorResponse, "description": "El Pokémon tiene registros médicos asociados"}},
)
def eliminar_pokemon(pokemon_id: PokemonId, service: PokemonService = Depends(get_pokemon_service)):
    service.eliminar_pokemon(pokemon_id)

@router.put(
    "/{pokemon_id}", response_model=PokemonResponse, status_code=status.HTTP_200_OK,
    summary="Actualizar Pokémon",
    description="Reemplaza los datos de un Pokémon. El entrenador indicado, si existe, debe estar registrado.",
    responses={**ERROR_422,
               404: {"model": ErrorResponse, "description": "Pokémon o entrenador no encontrado"},
               409: {"model": ErrorResponse, "description": "Conflicto al guardar la actualización"}},
)
def actualizar_pokemon(pokemon_id: PokemonId, datos: CrearPokemon, service: PokemonService = Depends(get_pokemon_service)):
    return service.actualizar_pokemon(pokemon_id, datos)

@router.patch(
    "/{pokemon_id}/asignar/{entrenador_id}", response_model=PokemonResponse, status_code=status.HTTP_200_OK,
    summary="Asignar entrenador a Pokémon",
    description="Asigna un entrenador existente a un Pokémon sin entrenador. Si ya tiene uno, usa transferir.",
    responses={**ERROR_422,
               400: {"model": ErrorResponse, "description": "El Pokémon ya tiene entrenador"},
               404: {"model": ErrorResponse, "description": "Pokémon o entrenador no encontrado"}},
)
def asignar_entrenador(pokemon_id: PokemonId, entrenador_id: EntrenadorId, service: PokemonService = Depends(get_pokemon_service)):
    return service.asignar_entrenador(pokemon_id, entrenador_id)

@router.patch(
    "/{pokemon_id}/transferir/{nuevo_entrenador_id}", response_model=PokemonResponse, status_code=status.HTTP_200_OK,
    summary="Transferir Pokémon a otro entrenador",
    description="Cambia la asignación a un entrenador existente. Rechaza la transferencia al mismo entrenador.",
    responses={**ERROR_422,
               400: {"model": ErrorResponse, "description": "El Pokémon ya pertenece al entrenador indicado"},
               404: {"model": ErrorResponse, "description": "Pokémon o entrenador no encontrado"}},
)
def transferir_entrenador(pokemon_id: PokemonId, nuevo_entrenador_id: EntrenadorId, service: PokemonService = Depends(get_pokemon_service)):
    return service.transferir_entrenador(pokemon_id, nuevo_entrenador_id)

@router.patch(
    "/{pokemon_id}/liberar", response_model=PokemonResponse, status_code=status.HTTP_200_OK,
    summary="Liberar Pokémon", description="Deja al Pokémon sin entrenador asignado.",
    responses={**ERROR_422, 404: {"model": ErrorResponse, "description": "Pokémon no encontrado"}},
)
def liberar_pokemon(pokemon_id: PokemonId, service: PokemonService = Depends(get_pokemon_service)):
    return service.liberar_pokemon(pokemon_id)

@router.patch(
    "/{pokemon_id}/stats", response_model=PokemonResponse, status_code=status.HTTP_200_OK,
    summary="Actualizar estadísticas de Pokémon",
    description="Actualiza nivel y puntos de vida; ambos deben estar entre 1 y 100.",
    responses={**ERROR_422, 404: {"model": ErrorResponse, "description": "Pokémon no encontrado"}},
)
def actualizar_stats(
    pokemon_id: PokemonId,
    nivel: int = Query(..., ge=1, le=100, examples=[25]),
    puntos_vida: int = Query(..., ge=1, le=100, examples=[90]),
    service: PokemonService = Depends(get_pokemon_service),
):
    return service.actualizar_stats(pokemon_id, nivel, puntos_vida)
