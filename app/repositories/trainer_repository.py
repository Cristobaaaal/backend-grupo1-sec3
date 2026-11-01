from app.domain.models import Entrenador
from uuid import UUID
from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.exceptions import ConflictError
from app.infrastructure.models import EntrenadorORM
from app.infrastructure.mappers import entrenador_a_domain
from sqlalchemy import select

class EntrenadorRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, entrenador: Entrenador) -> Entrenador:
        modelo = EntrenadorORM(
            id=str(entrenador.id),
            nombre=entrenador.nombre,
            nivel_experiencia=entrenador.nivel_experiencia,
            region_origen=entrenador.region_origen,
            medallas_obtenidas=entrenador.medallas_obtenidas,
        )
        self.db.add(modelo) # Añade el objeto para insertarlo
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError(
                "La operación entra en conflicto con los datos relacionados o existentes."
            ) from error
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(modelo)     # Recarga los valores de la db
        return entrenador_a_domain(modelo)  # Devuelve un Entrenador

    def get_all(self) -> List[Entrenador]:
        modelos = self.db.scalars(select(EntrenadorORM)).all()
        return [entrenador_a_domain(modelo) for modelo in modelos]

    def get_by_id(self, entrenador_id: UUID) -> Optional[Entrenador]:
        modelo = self.db.get(EntrenadorORM, str(entrenador_id))

        if modelo is None:
            return None

        return entrenador_a_domain(modelo)

    def delete(self, entrenador_id: UUID) -> bool:
        modelo = self.db.get(EntrenadorORM, str(entrenador_id))

        if modelo is None:
            return False

        self.db.delete(modelo)
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError(
                "La operación entra en conflicto con los datos relacionados o existentes."
            ) from error
        except Exception:
            self.db.rollback()
            raise
        return True

    def update(self, entrenador_id: UUID, updated_entrenador: Entrenador) -> Optional[Entrenador]:
        modelo = self.db.get(EntrenadorORM, str(entrenador_id))

        if modelo is None:
            return None

        modelo.nombre = updated_entrenador.nombre
        modelo.region_origen = updated_entrenador.region_origen
        modelo.medallas_obtenidas = updated_entrenador.medallas_obtenidas
        modelo.nivel_experiencia = updated_entrenador.nivel_experiencia

        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError(
                "La operación entra en conflicto con los datos relacionados o existentes."
            ) from error
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(modelo)

        return entrenador_a_domain(modelo)
