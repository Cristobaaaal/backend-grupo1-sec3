"""BD aislada y migrada, compartida por pytest y las regresiones unittest.

Usa una base cuyo nombre termina en _test. Cada contexto crea su propio schema,
lo prepara con Alembic y elimina únicamente ese schema al terminar.
"""

import os
import re
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.schema import CreateSchema, DropSchema

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEST_DATABASE_URL = (
    "postgresql+psycopg2://pokemon_test:pokemon_test@127.0.0.1:5433/pokemon_test"
)


@contextmanager
def migrated_postgres_database():
    """Entrega un motor real sobre un schema nuevo preparado con migraciones."""
    database_url = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql" or not (url.database or "").endswith(
        "_test"
    ):
        raise ValueError(
            "TEST_DATABASE_URL debe usar PostgreSQL y una base terminada en _test."
        )

    admin_engine = create_engine(
        url, connect_args={"connect_timeout": 5, "options": ""}
    )
    schema = f"tests_{uuid4().hex}"
    schema_created = False
    engine = None
    try:
        try:
            with admin_engine.begin() as connection:
                connection.execute(CreateSchema(schema))
            schema_created = True
        except OperationalError as error:
            raise RuntimeError(
                "No se pudo conectar a PostgreSQL de pruebas. Inicia Docker Desktop "
                "y ejecuta: docker compose -f tests/docker-compose.test.yml "
                "up -d --wait. También puedes configurar TEST_DATABASE_URL."
            ) from error

        environment = os.environ.copy()
        environment["DATABASE_URL"] = database_url
        environment["PGOPTIONS"] = f"-csearch_path={schema}"
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
            cwd=PROJECT_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(
                f"Las migraciones de la BD de pruebas fallaron:\n{result.stderr}"
            )

        engine = create_engine(
            database_url,
            connect_args={"connect_timeout": 5, "options": f"-csearch_path={schema}"},
        )
        with engine.connect() as connection:
            if connection.scalar(text("SELECT current_schema()")) != schema:
                raise RuntimeError("La conexión no está usando el schema de prueba.")
        yield engine
    finally:
        if engine is not None:
            engine.dispose()
        try:
            if schema_created:
                with admin_engine.begin() as connection:
                    connection.execute(DropSchema(schema, cascade=True))
        finally:
            admin_engine.dispose()


def clear_test_data(engine):
    """Limpia el schema aislado; conserva el historial de migraciones de Alembic."""
    with engine.connect() as connection:
        schema = connection.scalar(text("SELECT current_schema()"))
    if not (engine.url.database or "").endswith("_test") or not re.fullmatch(
        r"tests_[0-9a-f]{32}", schema or ""
    ):
        raise ValueError("La limpieza solo se permite dentro de un schema de prueba.")
    metadata = MetaData()
    metadata.reflect(bind=engine)
    with engine.begin() as connection:
        for table in reversed(metadata.sorted_tables):
            if table.name != "alembic_version":
                connection.execute(table.delete())
