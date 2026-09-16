from typing import List, Optional
from uuid import UUID
from app.domain.models import CentroPokemon
from app.schemas.schemas import CrearCentroPokemon


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

    def delete(self, centro_pokemon_id: UUID) -> bool:
        centro= self.get_by_id(centro_pokemon_id)
        if centro:
            self._db.remove(centro)
            return True
        return False
        
    def actualizar(self, centro_pokemon_id: UUID, datos: CrearCentroPokemon) -> Optional[CentroPokemon]:
        centro = self.get_by_id(centro_pokemon_id)
        if not centro:
            return None
        centro.nombre = datos.nombre
        centro.ciudad = datos.ciudad
        centro.capacidad_maxima = datos.capacidad_maxima
        centro.en_servicio = datos.en_servicio
        return centro

