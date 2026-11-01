from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.exceptions import ConflictError

from app.domain.models import Pokemon, TipoPokemon
from app.infrastructure.mappers import pokemon_a_domain
from app.infrastructure.models import PokemonORM
from app.schemas.schemas import CrearPokemon


class PokemonRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, pokemon: Pokemon) -> Pokemon:
        modelo = PokemonORM(
            id=str(pokemon.id),
            nombre=pokemon.nombre,
            tipo_principal=pokemon.tipo_principal.value,
            nivel=pokemon.nivel,
            puntos_vida=pokemon.puntos_vida,
            entrenador_id=(
                str(pokemon.entrenador_id)
                if pokemon.entrenador_id is not None
                else None
            ),
        )

        self.db.add(modelo)
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

        return pokemon_a_domain(modelo)

    def get_all(self) -> List[Pokemon]:
        modelos = self.db.scalars(select(PokemonORM)).all()
        return [pokemon_a_domain(modelo) for modelo in modelos]

    def get_by_id(self, pokemon_id: UUID) -> Optional[Pokemon]:
        modelo = self.db.get(PokemonORM, str(pokemon_id))

        if modelo is None:
            return None

        return pokemon_a_domain(modelo)

    def get_by_tipo(self, tipo: TipoPokemon) -> List[Pokemon]:
        consulta = select(PokemonORM).where(
            PokemonORM.tipo_principal == tipo.value
        )

        modelos = self.db.scalars(consulta).all()
        return [pokemon_a_domain(modelo) for modelo in modelos]

    def get_by_entrenador_id(self, entrenador_id: UUID) -> List[Pokemon]:
        consulta = select(PokemonORM).where(
            PokemonORM.entrenador_id == str(entrenador_id)
        )

        modelos = self.db.scalars(consulta).all()
        return [pokemon_a_domain(modelo) for modelo in modelos]

    def get_sin_entrenador(self) -> List[Pokemon]:
        consulta = select(PokemonORM).where(
            PokemonORM.entrenador_id.is_(None)
        )

        modelos = self.db.scalars(consulta).all()
        return [pokemon_a_domain(modelo) for modelo in modelos]

    def exists_by_entrenador_id(self, entrenador_id: UUID) -> bool:
        consulta = select(PokemonORM.id).where(
            PokemonORM.entrenador_id == str(entrenador_id)
        ).limit(1)

        return self.db.scalar(consulta) is not None

    def delete(self, pokemon_id: UUID) -> bool:
        modelo = self.db.get(PokemonORM, str(pokemon_id))

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

    def update(
        self,
        pokemon_id: UUID,
        datos: CrearPokemon,
    ) -> Optional[Pokemon]:
        modelo = self.db.get(PokemonORM, str(pokemon_id))

        if modelo is None:
            return None

        modelo.nombre = datos.nombre
        modelo.tipo_principal = datos.tipo_principal.value
        modelo.nivel = datos.nivel
        modelo.puntos_vida = datos.puntos_vida
        modelo.entrenador_id = (
            str(datos.entrenador_id)
            if datos.entrenador_id is not None
            else None
        )

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

        return pokemon_a_domain(modelo)

    def listar_paginado(
        self,
        tipo: Optional[TipoPokemon] = None,
        ordenar_por: str = "nombre",
        direccion: str = "asc",
        pagina: int = 1,
        limite: int = 20,
    ) -> tuple[List[Pokemon], int]:
        columnas = {
            "nombre": PokemonORM.nombre,
            "nivel": PokemonORM.nivel,
            "puntos_vida": PokemonORM.puntos_vida,
        }

        if ordenar_por not in columnas:
            raise ValueError("Columna de ordenamiento inválida.")
        if direccion not in ("asc", "desc"):
            raise ValueError("Dirección de ordenamiento inválida.")
        if pagina < 1 or not 1 <= limite <= 100:
            raise ValueError("Paginación inválida.")

        consulta = select(PokemonORM)
        conteo = select(func.count()).select_from(PokemonORM)

        if tipo is not None:
            filtro = PokemonORM.tipo_principal == tipo.value
            consulta = consulta.where(filtro)
            conteo = conteo.where(filtro)

        total = self.db.scalar(conteo)

        columna = columnas[ordenar_por]
        orden = columna.asc() if direccion == "asc" else columna.desc()

        consulta = (
            consulta
            .order_by(orden, PokemonORM.id)
            .offset((pagina - 1) * limite)
            .limit(limite)
        )

        modelos = self.db.scalars(consulta).all()
        items = [pokemon_a_domain(modelo) for modelo in modelos]

        return items, total
