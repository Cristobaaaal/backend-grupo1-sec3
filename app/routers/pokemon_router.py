from fastapi import APIRouter, status
from typing import List
from uuid import UUID
from app.schemas.schemas import CrearPokemon
from app.domain.models import Pokemon
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

@router.get("/{pokemon_id}", response_model=Pokemon, status_code=status.HTTP_200_OK) #responde las peticiones para buscar por el id del pokemon 
def obtener_pokemon(pokemon_id: UUID):
    return _service.obtener_por_id(pokemon_id) #retorna el pokemon con el id

@router.get("/entrenador/{entrenador_id}", response_model=List[Pokemon], status_code=status.HTTP_200_OK) #responde a las peticiones para buscar pokemones por el id del entrenador
def obtener_pokemones_por_entrenador(entrenador_id: UUID):
    return _service.obtener_por_entrenador(entrenador_id)
