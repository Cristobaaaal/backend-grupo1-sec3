from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.domain.models import RegistroMedico
from app.infrastructure.mappers import registro_a_domain
from app.infrastructure.models import RegistroMedicoORM
from app.schemas.schemas import CrearRegistroMedico


class RegistroMedicoRepository:
    def __init__(self, db: Session):
        self.db = db

    def guardar(self, datos: CrearRegistroMedico) -> RegistroMedico:
        modelo = RegistroMedicoORM(
            id=str(uuid4()),
            pokemon_id=str(datos.pokemon_id),
            centro_id=str(datos.centro_id),
            diagnostico=datos.diagnostico,
            fecha_ingreso=datos.fecha_ingreso,
            estado=datos.estado.value,
            costo=datos.costo,
        )
        self.db.add(modelo)
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError(
                "No se pudo guardar el registro: comprueba sus referencias."
            ) from error
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(modelo)
        return registro_a_domain(modelo)

    def obtener_por_id(self, registro_id: UUID) -> Optional[RegistroMedico]:
        modelo = self.db.get(RegistroMedicoORM, str(registro_id))
        if modelo is None:
            return None
        return registro_a_domain(modelo)

    def obtener_todos(self) -> List[RegistroMedico]:
        modelos = self.db.scalars(select(RegistroMedicoORM)).all()
        return [registro_a_domain(modelo) for modelo in modelos]

    def actualizar(
        self, registro_id: UUID, datos: CrearRegistroMedico
    ) -> Optional[RegistroMedico]:
        modelo = self.db.get(RegistroMedicoORM, str(registro_id))
        if modelo is None:
            return None
        modelo.pokemon_id = str(datos.pokemon_id)
        modelo.centro_id = str(datos.centro_id)
        modelo.diagnostico = datos.diagnostico
        modelo.fecha_ingreso = datos.fecha_ingreso
        modelo.estado = datos.estado.value
        modelo.costo = datos.costo
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError(
                "No se pudo actualizar el registro: comprueba sus referencias."
            ) from error
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(modelo)
        return registro_a_domain(modelo)

    def eliminar(self, registro_id: UUID) -> bool:
        modelo = self.db.get(RegistroMedicoORM, str(registro_id))
        if modelo is None:
            return False
        self.db.delete(modelo)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return True

    def exists_by_pokemon_id(self, pokemon_id: UUID) -> bool:
        consulta = select(RegistroMedicoORM.id).where(
            RegistroMedicoORM.pokemon_id == str(pokemon_id)
        ).limit(1)
        return self.db.scalar(consulta) is not None

    def exists_by_centro_id(self, centro_id: UUID) -> bool:
        consulta = select(RegistroMedicoORM.id).where(
            RegistroMedicoORM.centro_id == str(centro_id)
        ).limit(1)
        return self.db.scalar(consulta) is not None
