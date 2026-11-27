from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.infrastructure.database import Base


class EntrenadorORM(Base):
    __tablename__ = "entrenadores"

    id = Column(String(36), primary_key=True)
    nombre = Column(String(100), nullable=False)
    nivel_experiencia = Column(Integer, nullable=False)
    region_origen = Column(String(100), nullable=False)
    medallas_obtenidas = Column(Integer, nullable=False)

    pokemones = relationship(
        "PokemonORM",
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
        String(36), ForeignKey("entrenadores.id"), nullable=True, index=True
    )

    entrenador = relationship("EntrenadorORM", back_populates="pokemones")

    registros_medicos = relationship(
        "RegistroMedicoORM",
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

    registros_medicos = relationship(
        "RegistroMedicoORM",
        back_populates="centro",
        passive_deletes="all",
    )


class RegistroMedicoORM(Base):
    __tablename__ = "registros_medicos"

    id = Column(String(36), primary_key=True)
    pokemon_id = Column(
        String(36), ForeignKey("pokemones.id"), nullable=False, index=True
    )

    centro_id = Column(
        String(36), ForeignKey("centros_pokemon.id"), nullable=False, index=True
    )
    diagnostico = Column(String(1000), nullable=False)
    fecha_ingreso = Column(Date, nullable=False)
    estado = Column(String(20), nullable=False, index=True)
    costo = Column(Integer, nullable=False)

    pokemon = relationship("PokemonORM", back_populates="registros_medicos")
    centro = relationship("CentroPokemonORM", back_populates="registros_medicos")


class UsuarioORM(Base):
    __tablename__ = "usuarios"

    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre_completo = Column(String(150), nullable=False)
    rol = Column(String(50), nullable=False, index=True)
    activo = Column(Boolean, default=True, nullable=False)
    intentos_fallidos = Column(Integer, default=0, nullable=False)
    bloqueado_hasta = Column(DateTime, nullable=True)
    token_version = Column(Integer, nullable=False, default=0, server_default="0")

    refresh_tokens = relationship(
        "RefreshTokenORM",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )
    password_reset_tokens = relationship(
        "PasswordResetTokenORM",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )


class RefreshTokenORM(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    usuario_id = Column(
        String(36),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expira_en = Column(DateTime, nullable=False)
    revocado = Column(Boolean, default=False, nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
    familia_id = Column(
        String(36), ForeignKey("auth_sessions.id"), nullable=True, index=True
    )

    usuario = relationship("UsuarioORM", back_populates="refresh_tokens")


class PasswordResetTokenORM(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(String(36), primary_key=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    usuario_id = Column(
        String(36),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expira_en = Column(DateTime, nullable=False)
    usado = Column(Boolean, default=False, nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)

    usuario = relationship("UsuarioORM", back_populates="password_reset_tokens")


class AuthSessionORM(Base):
    __tablename__ = "auth_sessions"

    id = Column(String(36), primary_key=True)
    usuario_id = Column(
        String(36),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    revocada = Column(Boolean, nullable=False, default=False, server_default="0")
    expira_en = Column(DateTime, nullable=False)


class AuthRateLimitORM(Base):
    __tablename__ = "auth_rate_limits"

    clave = Column(String(64), primary_key=True)
    intentos = Column(Integer, nullable=False, default=0)
