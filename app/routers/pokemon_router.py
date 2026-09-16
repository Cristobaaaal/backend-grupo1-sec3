from fastapi import APIRouter, status, HTTPException, Query
from typing import List
from uuid import UUID
from app.schemas.schemas import CrearPokemon
from app.domain.models import Pokemon, TipoPokemon
from app.services.pokemon_service import PokemonService 
from app.repositories.pokemon_repository import PokemonRepository

router = APIRouter(prefix="/pokemones", tags=["Pokemones"]) #todas las urls q tengan "pokemones" van a tener la etiqueta de "Pokemones"
_repo = PokemonRepository() #se instancia la clase PokemonRepository
_service = PokemonService(_repo) #se instancia la clase PokemonService

@router.post("/", response_model=Pokemon, status_code=status.HTTP_201_CREATED) #responde las peticiones para crear un pokemon
def crear_pokemon(datos: CrearPokemon):
    return _service.crear_pokemon(datos)

@router.get("/", response_model=List[Pokemon], status_code=status.HTTP_200_OK) #responde las peticiones para buscar los pokemones
def obtener_pokemones():
    return _service.obtener_todos() #retorna todos los pokemones

@router.get("/sin-entrenador", response_model=List[Pokemon], status_code=status.HTTP_200_OK)
def obtener_sin_entrenador():
    return _service.obtener_sin_entrenador()

@router.get("/tipo/{tipo}", response_model=List[Pokemon], status_code=status.HTTP_200_OK)
def obtener_por_tipo(tipo: TipoPokemon):
    return _service.obtener_por_tipo(tipo)

@router.get("/{pokemon_id}", response_model=Pokemon, status_code=status.HTTP_200_OK) #responde las peticiones para buscar por el id del pokemon 
def obtener_pokemon(pokemon_id: UUID):
    return _service.obtener_por_id(pokemon_id) #retorna el pokemon con el id

@router.get("/entrenador/{entrenador_id}", response_model=List[Pokemon], status_code=status.HTTP_200_OK) #responde a las peticiones para buscar pokemones por el id del entrenador
def obtener_pokemones_por_entrenador(entrenador_id: UUID):
    return _service.obtener_por_entrenador(entrenador_id)

@router.delete("/{pokemon_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_pokemon(pokemon_id: UUID):
    try:
        return _service.eliminar_pokemon(pokemon_id)
    except ValueError as e:
        raise HTTPException(
             status_code=status.HTTP_404_NOT_FOUND,
             detail=str(e)
        )

@router.put("/{pokemon_id}", response_model=Pokemon, status_code=status.HTTP_200_OK)
def actualizar_pokemon(pokemon_id: UUID, datos: CrearPokemon):
    try:
        return _service.actualizar_pokemon(pokemon_id, datos)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.patch("/{pokemon_id}/asignar/{entrenador_id}", response_model=Pokemon, status_code=status.HTTP_200_OK)
def asignar_entrenador(pokemon_id: UUID, entrenador_id: UUID):
    try:
        return _service.asignar_entrenador(pokemon_id, entrenador_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.patch("/{pokemon_id}/transferir/{nuevo_entrenador_id}", response_model=Pokemon, status_code=status.HTTP_200_OK)
def transferir_entrenador(pokemon_id: UUID, nuevo_entrenador_id: UUID):
    try:
        return _service.transferir_entrenador(pokemon_id, nuevo_entrenador_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.patch("/{pokemon_id}/liberar", response_model=Pokemon, status_code=status.HTTP_200_OK)
def liberar_pokemon(pokemon_id: UUID):
    try:
        return _service.liberar_pokemon(pokemon_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.patch("/{pokemon_id}/stats", response_model=Pokemon, status_code=status.HTTP_200_OK)
def actualizar_stats(
    pokemon_id: UUID,
    nivel: int = Query(..., ge=1, le=100),
    puntos_vida: int = Query(..., ge=1, le=100)
):
    try:
        return _service.actualizar_stats(pokemon_id, nivel, puntos_vida)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e) else status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )