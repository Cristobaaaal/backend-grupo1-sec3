from app.domain.models import Pokemon, TipoPokemon
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

    def obtener_por_tipo(self, tipo: TipoPokemon) -> List[Pokemon]:
        return self.repository.get_by_tipo(tipo)

    def obtener_por_entrenador(self, entrenador_id: UUID) -> List[Pokemon]:
        return self.repository.get_by_entrenador_id(entrenador_id)

    def obtener_sin_entrenador(self) -> List[Pokemon]:
        return self.repository.get_sin_entrenador()

    def asignar_entrenador(self, pokemon_id: UUID, entrenador_id: UUID) -> Pokemon:
        pokemon = self.obtener_por_id(pokemon_id)
        pokemon.entrenador_id = entrenador_id
        return pokemon

    def transferir_entrenador(self, pokemon_id: UUID, nuevo_entrenador_id: UUID) -> Pokemon:
        pokemon = self.obtener_por_id(pokemon_id)
        pokemon.entrenador_id = nuevo_entrenador_id
        return pokemon

    def liberar_pokemon(self, pokemon_id: UUID) -> Pokemon:
        pokemon = self.obtener_por_id(pokemon_id)
        pokemon.entrenador_id = None
        return pokemon

    def actualizar_stats(self, pokemon_id: UUID, nivel: int, puntos_vida: int) -> Pokemon:
        if not (1 <= nivel <= 100):
            raise ValueError("El nivel debe estar entre 1 y 100.")
        if not (1 <= puntos_vida <= 100):
            raise ValueError("Los puntos de vida deben estar entre 1 y 100.")
        pokemon = self.obtener_por_id(pokemon_id)
        pokemon.nivel = nivel
        pokemon.puntos_vida = puntos_vida
        return pokemon

    def eliminar_pokemon(self, pokemon_id: UUID) -> None:
        eliminado = self.repository.delete(pokemon_id)
        if not eliminado:
            raise ValueError(f"pokemon with id {pokemon_id} not found.")

    def actualizar_pokemon(self, pokemon_id: UUID, datos: CrearPokemon) -> Pokemon:
        pokemon_actualizado = self.repository.update(pokemon_id, datos)
        if not pokemon_actualizado:
            raise ValueError(f"pokemon with id {pokemon_id} not found.")
        return pokemon_actualizado