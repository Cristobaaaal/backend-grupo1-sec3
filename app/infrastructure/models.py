from sqlalchemy import ForeignKey, String, Date # Tipo de fecha de sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database import Base
from datetime import date # Tipo de fecha de python



class EntrenadorORM(Base):
    __tablename__ = "entrenadores"
    # Mismos atributos que la tabla de /domain/models.py
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    nivel_experiencia: Mapped[int] = mapped_column()
    region_origen: Mapped[str] = mapped_column(String(100))
    medallas_obtenidas: Mapped[int] = mapped_column()

    pokemones: Mapped[list["PokemonORM"]] = relationship( # nombre(pokemones)
        back_populates="entrenador", # conecta con atributo entrenador de PokemonORM
        passive_deletes="all",
    )

class PokemonORM(Base):
    __tablename__ = "pokemones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    tipo_principal: Mapped[str] = mapped_column(String(20), index=True) # Guarda valores como "FUEGO, índice(index)
    nivel: Mapped[int] = mapped_column()
    puntos_vida: Mapped[int] = mapped_column()

    entrenador_id: Mapped[str | None] = mapped_column( # Permitir pokemón sin entrenador (opcional)
        String(36),
        ForeignKey("entrenadores.id"),
        index=True
    )

    entrenador: Mapped["EntrenadorORM | None"] = relationship( # Nombre(entrenador) | None, 1 o ninguno
        back_populates="pokemones"
    )

class CentroPokemonORM(Base):
    __tablename__ = "centros_pokemon"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    ciudad: Mapped[str] = mapped_column(String(100), index=True)
    capacidad_maxima: Mapped[int] = mapped_column()
    en_servicio: Mapped[bool] = mapped_column()

class RegistroMedicoORM(Base):
    __tablename__ = "registros_medicos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    pokemon_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("pokemones.id"),
        index=True
    )

    centro_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("centros_pokemon.id"),
        index=True
    )
    diagnostico: Mapped[str] = mapped_column(String(1000))
    fecha_ingreso: Mapped[date] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(String(20), index=True)
    costo: Mapped[int] = mapped_column()
