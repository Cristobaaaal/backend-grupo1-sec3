from app.domain.models import Pokemon
from app.repositories.pokemon_repository import PokemonRepository
from app.schemas.schemas import CrearPokemon
from typing import List
from uuid import UUID, uuid4

class PokemonService:
    def __init__(self, repository: PokemonRepository):
        self.repository = repository

    def crear_pokemon(self, datos: CrearPokemon) -> Pokemon: # es el tipo de dato q se espera
        pokemon = Pokemon(
            id=uuid4(),
            nombre=datos.nombre,
            tipo_principal=datos.tipo_principal,
            nivel=datos.nivel,
            puntos_vida=datos.puntos_vida,
            entrenador_id=datos.entrenador_id
        )
        return self.repository.save(pokemon)
    
    def obtener_todos(self) -> List[Pokemon]:
        return self.repository.get_all() #llama a todos los pokemones

    def obtener_por_id(self, pokemon_id: UUID) -> Pokemon:
        pokemon = self.repository.get_by_id(pokemon_id) #lo busca por id
        if not pokemon:
            raise ValueError(f"pokemon with id {pokemon_id} not found.") #si no esta le manda un error
        return pokemon

    def obtener_por_entrenador(self, entrenador_id: UUID) -> List[Pokemon]:
        return self.repository.get_by_entrenador_id(entrenador_id)