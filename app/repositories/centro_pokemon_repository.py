from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.domain.models import CentroPokemon
from app.infrastructure.mappers import centro_a_domain
from app.infrastructure.models import CentroPokemonORM
from app.schemas.schemas import CrearCentroPokemon


class CentroPokemonRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, centro: CentroPokemon) -> CentroPokemon:
        modelo = CentroPokemonORM(
            id=str(centro.id),
            nombre=centro.nombre,
            ciudad=centro.ciudad,
            capacidad_maxima=centro.capacidad_maxima,
            en_servicio=centro.en_servicio,
        )
        self.db.add(modelo)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(modelo)
        return centro_a_domain(modelo)

    def get_all(self) -> List[CentroPokemon]:
        modelos = self.db.scalars(select(CentroPokemonORM)).all()
        return [centro_a_domain(modelo) for modelo in modelos]

    def get_by_id(self, centro_id: UUID) -> Optional[CentroPokemon]:
        modelo = self.db.get(CentroPokemonORM, str(centro_id))
        if modelo is None:
            return None
        return centro_a_domain(modelo)

    def get_by_ciudad(self, ciudad: str) -> List[CentroPokemon]:
        consulta = select(CentroPokemonORM).where(
            func.lower(CentroPokemonORM.ciudad) == ciudad.lower()
        )
        modelos = self.db.scalars(consulta).all()
        return [centro_a_domain(modelo) for modelo in modelos]

    def delete(self, centro_pokemon_id: UUID) -> bool:
        modelo = self.db.get(CentroPokemonORM, str(centro_pokemon_id))
        if modelo is None:
            return False
        self.db.delete(modelo)
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError(
                "No se puede eliminar el centro: tiene registros asociados."
            ) from error
        except Exception:
            self.db.rollback()
            raise
        return True

    def actualizar(
        self, centro_pokemon_id: UUID, datos: CrearCentroPokemon
    ) -> Optional[CentroPokemon]:
        modelo = self.db.get(CentroPokemonORM, str(centro_pokemon_id))
        if modelo is None:
            return None
        modelo.nombre = datos.nombre
        modelo.ciudad = datos.ciudad
        modelo.capacidad_maxima = datos.capacidad_maxima
        modelo.en_servicio = datos.en_servicio
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(modelo)
        return centro_a_domain(modelo)
