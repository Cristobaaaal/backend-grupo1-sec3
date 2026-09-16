from app.domain.models import Pokemon, TipoPokemon
from uuid import UUID
from typing import List, Optional
from app.schemas.schemas import CrearPokemon

class PokemonRepository:
    def __init__(self):
        self._db: List[Pokemon] = []

    def save(self, pokemon: Pokemon) -> Pokemon:
        self._db.append(pokemon) #se agrega el pokemon a la lista de pokemones 
        return pokemon  #te devuelve el pokemon agregado

    def get_all(self) -> List[Pokemon]:
        return self._db #va a buscarte todos los pokemones que estan en la lista

    def get_by_id(self, pokemon_id: UUID) -> Optional[Pokemon]:
        for pokemon in self._db:
            if pokemon.id == pokemon_id: #recorre la lista buscando el pokemon con ese id
                return pokemon #te lo devuelve si lo encuentra
        return None

    def get_by_tipo(self, tipo: TipoPokemon) -> List[Pokemon]:
        return [p for p in self._db if p.tipo_principal == tipo]

    def get_by_entrenador_id(self, entrenador_id: UUID) -> List[Pokemon]: #sirve para encontrar los pokemones que pertenecen a cierto entrenador en especifico
        return [p for p in self._db if p.entrenador_id == entrenador_id]

    def get_sin_entrenador(self) -> List[Pokemon]:
        return [p for p in self._db if p.entrenador_id is None]

    def delete(self, pokemon_id: UUID) -> bool:
        pokemon = self.get_by_id(pokemon_id)
        if pokemon:
            self._db.remove(pokemon)
            return True
        return False

    def update(self, pokemon_id: UUID, datos: CrearPokemon) -> Pokemon:
        pokemon = self.get_by_id(pokemon_id)
        if not pokemon:
            return None
        pokemon.nombre = datos.nombre
        pokemon.tipo_principal = datos.tipo_principal
        pokemon.nivel = datos.nivel
        pokemon.puntos_vida = datos.puntos_vida
        pokemon.entrenador_id = datos.entrenador_id
        return pokemon