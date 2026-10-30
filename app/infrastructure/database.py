import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite:///./pokemon.db"
)  # Usamos sqlite y el archivo pokemon.db

engine = create_engine(  # Conexión con la db
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")  # Ejecuta esto cada vez que se abra una conexión
def activar_claves_foraneas(
    dbapi_connection, connection_record
):  # Recibe la conexión abierta
    cursor = dbapi_connection.cursor()  # Objeto para ejecutar SQL
    try:
        cursor.execute("PRAGMA foreign_keys=ON")  # Comprueba FK
    finally:
        cursor.close()


SessionLocal = sessionmaker(  # Sesiones para consultar, guardar y confirmar operaciones
    bind=engine,
    autoflush=False,  # Evita auto enviar cambios antes de las consultas
)


class Base(DeclarativeBase):  # Base de modelos ORM (tablas)
    pass

def get_db():
    db = SessionLocal() # Crea la sesión
    try:
        yield db   # "Entregar" la sesión
    finally:
        db.close() # Después de usarla se cierra
