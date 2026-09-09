from typing import List, Optional
from uuid import UUID
from app.domain.models import CentroPokemon


class CentroPokemonRepository:
    def __init__(self):
        self._db: List[CentroPokemon] = [] # Lista vacía que almacena solo objetos tipo CentroPokemon

    def save(self, centro: CentroPokemon) -> CentroPokemon: 
        self._db.append(centro) # Guarda al final de la lista 
        return centro

    def get_all(self) -> List[CentroPokemon]:
        return self._db  # Retorna todo lo ingresado en la lista

    def get_by_id(self, centro_id: UUID) -> Optional[CentroPokemon]:
        for c in self._db: # Recorre la lista y convierten momentáneamente en "c" a un objeto de la lista
            if c.id == centro_id: # Compara el objeto de la lista "c" con el que pide el usuario
                return c
        return None

    def get_by_ciudad(self, ciudad: str) -> List[CentroPokemon]:
        centros_encontrados = []
        for c in self._db:
            if c.ciudad.lower() == ciudad.lower():
                centros_encontrados.append(c)
        return centros_encontrados