from fastapi import APIRouter, status, Query
from typing import List, Optional
from uuid import UUID
from app.schemas.schemas import CrearPokemon, PaginatedResponse
from app.domain.models import Pokemon, TipoPokemon
from app.services.pokemon_service import PokemonService 
from app.core.dependencies import pokemon_repo, trainer_repo

router = APIRouter(prefix="/pokemones", tags=["Pokemones"]) #todas las urls q tengan "pokemones" van a tener la etiqueta de "Pokemones"
_service = PokemonService(pokemon_repo, trainer_repo) #se instancia la clase PokemonService con los repos compartidos

@router.post("/", response_model=Pokemon, status_code=status.HTTP_201_CREATED) #responde las peticiones para crear un pokemon
def crear_pokemon(datos: CrearPokemon):
    return _service.crear_pokemon(datos)

@router.get("/", response_model=PaginatedResponse[Pokemon], status_code=status.HTTP_200_OK) #responde las peticiones para buscar los pokemones
def obtener_pokemones(
    tipo: Optional[TipoPokemon] = Query(None, description="Filtra por tipo_principal"),
    ordenar_por: str = Query("nombre", description="nombre | nivel | puntos_vida"),
    direccion: str = Query("asc", description="asc o desc"),
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=100),
):
    return _service.listar_paginado(
        tipo=tipo, ordenar_por=ordenar_por, direccion=direccion, pagina=pagina, limite=limite
    )

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
     return _service.eliminar_pokemon(pokemon_id)

@router.put("/{pokemon_id}", response_model=Pokemon, status_code=status.HTTP_200_OK)
def actualizar_pokemon(pokemon_id: UUID, datos: CrearPokemon):
    return _service.actualizar_pokemon(pokemon_id, datos)

@router.patch("/{pokemon_id}/asignar/{entrenador_id}", response_model=Pokemon, status_code=status.HTTP_200_OK)
def asignar_entrenador(pokemon_id: UUID, entrenador_id: UUID):
    return _service.asignar_entrenador(pokemon_id, entrenador_id)

@router.patch("/{pokemon_id}/transferir/{nuevo_entrenador_id}", response_model=Pokemon, status_code=status.HTTP_200_OK)
def transferir_entrenador(pokemon_id: UUID, nuevo_entrenador_id: UUID):
    return _service.transferir_entrenador(pokemon_id, nuevo_entrenador_id)

@router.patch("/{pokemon_id}/liberar", response_model=Pokemon, status_code=status.HTTP_200_OK)
def liberar_pokemon(pokemon_id: UUID):
    return _service.liberar_pokemon(pokemon_id)

@router.patch("/{pokemon_id}/stats", response_model=Pokemon, status_code=status.HTTP_200_OK)
def actualizar_stats(
    pokemon_id: UUID,
    nivel: int = Query(..., ge=1, le=100),
    puntos_vida: int = Query(..., ge=1, le=100)
):
    return _service.actualizar_stats(pokemon_id, nivel, puntos_vida)