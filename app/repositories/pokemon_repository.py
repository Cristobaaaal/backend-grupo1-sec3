from app.domain.models import Pokemon
from uuid import UUID
from typing import List, Optional

class PokemonRepository:
    def __init__(self):
        self._db: List[Pokemon] = [] # Database privado (db, _: privado) definido como lista

    def save(self, pokemon: Pokemon) -> Pokemon: # Recibe objeto Pokemon y devuelve lo mismo
        self._db.append(pokemon) # Agrega el Pokemón al final de la lista
        return pokemon # Devuelve la entidad guardada

    def get_all(self) -> List[Pokemon]: # Retorna la lista completa
        return self._db

    def get_by_id(self, pokemon_id: UUID) -> Optional[Pokemon]:
        for pokemon in self._db:
            if pokemon.id == pokemon_id: # Compara el UUID del pokemon actual con el solicitado
              return pokemon
        return None # Si no se encuentra almacenado retorna que no existe

    def get_by_entrenador_id(self, entrenador_id: UUID) -> List[Pokemon]: # Funciona para ver que pokemones tiene el entrenador
        resultado = [] #

        for p in self._db: # Revisa los pokemones de la db y toma un pokemon "p"
            if p.entrenador_id == entrenador_id: 
                resultado.append(p)
        return resultado