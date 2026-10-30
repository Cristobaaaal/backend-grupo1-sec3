from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.infrastructure.database import Base



class EntrenadorORM(Base):
    __tablename__ = "entrenadores"

    id = Column(String(36), primary_key=True)
    nombre = Column(String(100), nullable=False)
    nivel_experiencia = Column(Integer, nullable=False)
    region_origen = Column(String(100), nullable=False)
    medallas_obtenidas = Column(Integer, nullable=False)

    pokemones = relationship("PokemonORM",
        back_populates="entrenador",
        passive_deletes="all",
    )

class PokemonORM(Base):
    __tablename__ = "pokemones"

    id = Column(String(36), primary_key=True)
    nombre = Column(String(100), nullable=False)
    tipo_principal = Column(String(20), nullable=False, index=True)
    nivel = Column(Integer, nullable=False)
    puntos_vida = Column(Integer, nullable=False)

    entrenador_id = Column(
        String(36),
        ForeignKey("entrenadores.id"),
        nullable=True,
        index=True
    )

    entrenador = relationship("EntrenadorORM",
        back_populates="pokemones"
    )

    registros_medicos = relationship("RegistroMedicoORM",
        back_populates="pokemon",
        passive_deletes="all",
    )
class CentroPokemonORM(Base):
    __tablename__ = "centros_pokemon"

    id = Column(String(36), primary_key=True)
    nombre = Column(String(100), nullable=False)
    ciudad = Column(String(100), nullable=False, index=True)
    capacidad_maxima = Column(Integer, nullable=False)
    en_servicio = Column(Boolean, nullable=False)

    registros_medicos = relationship("RegistroMedicoORM",
        back_populates = "centro",
        passive_deletes="all",
    )

class RegistroMedicoORM(Base):
    __tablename__ = "registros_medicos"

    id = Column(String(36), primary_key=True)
    pokemon_id = Column(
        String(36),
        ForeignKey("pokemones.id"),
        nullable=False,
        index=True
    )

    centro_id = Column(
        String(36),
        ForeignKey("centros_pokemon.id"),
        nullable=False,
        index=True
    )
    diagnostico = Column(String(1000), nullable=False)
    fecha_ingreso = Column(Date, nullable=False)
    estado = Column(String(20), nullable=False, index=True)
    costo = Column(Integer, nullable=False)

    pokemon = relationship("PokemonORM",
        back_populates = "registros_medicos"
    )
    centro = relationship("CentroPokemonORM",
        back_populates ="registros_medicos"
    )
