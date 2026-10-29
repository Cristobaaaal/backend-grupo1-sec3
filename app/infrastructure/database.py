from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = "sqlite:///./pokemon.db" # Usamos sqlite y el archivo pokemon.db

engine = create_engine(  # Conexión con la db
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker( # Sesiones para consultar, guardar y confirmar operaciones
    bind=engine,
    autoflush= False, # Evita auto enviar cambios antes de las consultas
)

class Base(DeclarativeBase): # Base de modelos ORM (tablas)
    pass
