"""Fixtures de PostgreSQL: solo se conectan cuando un test las solicita."""

import pytest
from sqlalchemy.orm import Session

from tests.database import clear_test_data, migrated_postgres_database


@pytest.fixture(scope="session")
def migrated_database():
    """Aplica Alembic en un schema exclusivo para esta ejecución de pytest."""
    with migrated_postgres_database() as engine:
        yield engine


@pytest.fixture
def clean_database(migrated_database):
    """Entrega tablas vacías y limpia también cuando una prueba falla."""
    clear_test_data(migrated_database)
    try:
        yield migrated_database
    finally:
        clear_test_data(migrated_database)


@pytest.fixture
def db_session(clean_database):
    """Abre una sesión real; los commits de los repositorios se ejecutan."""
    with Session(clean_database) as session:
        try:
            yield session
        finally:
            session.rollback()
