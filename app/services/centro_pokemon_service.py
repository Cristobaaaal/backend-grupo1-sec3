from typing import List
from uuid import UUID, uuid4
from app.domain.models import CentroPokemon
from app.repositories.centro_pokemon_repository import CentroPokemonRepository
from app.schemas.schemas import CrearCentroPokemon


class CentroPokemonService:
    def __init__(self, centro_repo: CentroPokemonRepository):
        self.centro_repo = centro_repo

    def crear_centro(self, datos: CrearCentroPokemon) -> CentroPokemon:
        if datos.capacidad_maxima <= 0:
            raise ValueError("La capacidad máxima del centro debe ser mayor a 0.")

        nuevo_centro = CentroPokemon(
            id=uuid4(),
            nombre=datos.nombre,
            ciudad=datos.ciudad,
            capacidad_maxima=datos.capacidad_maxima,
            en_servicio=datos.en_servicio,
        )

        return self.centro_repo.save(nuevo_centro)

    def obtener_todos(self) -> List[CentroPokemon]:
        return self.centro_repo.get_all()

    def obtener_por_id(self, centro_id: UUID) -> CentroPokemon:
        centro = self.centro_repo.get_by_id(centro_id)
        if not centro:
            raise ValueError(f"Centro Pokémon con id {centro_id} no encontrado.")
        return centro

    def obtener_por_ciudad(self, ciudad: str) -> List[CentroPokemon]:
        return self.centro_repo.get_by_ciudad(ciudad)