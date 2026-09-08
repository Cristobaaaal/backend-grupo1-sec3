from app.domain.models import Pokemon
from uuid import UUID
from typing import List, Optional

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

    def get_by_entrenador_id(self, entrenador_id: UUID) -> List[Pokemon]: #sirve para encontrar los pokemones que pertenecen a cierto entrenador en especifico
        return [p for p in self._db if p.entrenador_id == entrenador_id]