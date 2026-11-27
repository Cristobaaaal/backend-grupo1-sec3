"""Carga inicial real: repetición sin duplicados y rollback ante un conflicto."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.models import (
    CentroPokemonORM,
    EntrenadorORM,
    PokemonORM,
    RegistroMedicoORM,
    UsuarioORM,
)
from app.infrastructure.seeders import seed

pytestmark = pytest.mark.integration
MODELOS_Y_CANTIDADES = (
    (UsuarioORM, 3),
    (EntrenadorORM, 2),
    (CentroPokemonORM, 2),
    (PokemonORM, 2),
    (RegistroMedicoORM, 2),
)


@pytest.fixture
def seed_de_prueba(clean_database, monkeypatch):
    """Dirige únicamente la fábrica de sesiones al PostgreSQL migrado de pruebas."""
    monkeypatch.setattr(seed, "SessionLocal", sessionmaker(bind=clean_database))
    return clean_database


def test_seed_es_repetible_y_conserva_cambios_existentes(seed_de_prueba, capsys):
    """Dos ejecuciones no duplican ni sobrescriben usuarios modificados."""
    seed.ejecutar_seed()
    assert "11 creados, 0 existentes" in capsys.readouterr().out
    admin_id = str(UUID("50000000-0000-4000-8000-000000000001"))
    with Session(seed_de_prueba) as session:
        admin = session.get(UsuarioORM, admin_id)
        admin.nombre_completo = "Administrador actualizado"
        admin.activo = False
        session.commit()

    seed.ejecutar_seed()

    assert "0 creados, 11 existentes" in capsys.readouterr().out
    with Session(seed_de_prueba) as session:
        for modelo, cantidad in MODELOS_Y_CANTIDADES:
            assert session.scalar(select(func.count()).select_from(modelo)) == cantidad
        admin = session.get(UsuarioORM, admin_id)
        assert admin.nombre_completo == "Administrador actualizado"
        assert admin.activo is False
        assert set(session.scalars(select(UsuarioORM.rol))) == {
            "ADMIN",
            "VETERINARIO",
            "ENTRENADOR",
        }
        assert (
            session.scalar(
                select(func.count())
                .select_from(RegistroMedicoORM)
                .join(PokemonORM, RegistroMedicoORM.pokemon_id == PokemonORM.id)
                .join(
                    CentroPokemonORM, RegistroMedicoORM.centro_id == CentroPokemonORM.id
                )
            )
            == 2
        )


def test_seed_conflictivo_revierte_la_carga_y_conserva_la_cuenta_original(
    seed_de_prueba,
):
    """Un correo ya ocupado con otro ID impide dejar una carga parcial."""
    existente_id = str(uuid4())
    with Session(seed_de_prueba) as session:
        session.add(
            UsuarioORM(
                id=existente_id,
                email="entrenador@pokemon.com",
                password_hash="hash-ficticio",
                nombre_completo="Cuenta existente",
                rol="ENTRENADOR",
                activo=True,
            )
        )
        session.commit()

    with pytest.raises(IntegrityError):
        seed.ejecutar_seed()

    with Session(seed_de_prueba) as session:
        assert list(session.scalars(select(UsuarioORM.id))) == [existente_id]
        assert (
            session.get(UsuarioORM, existente_id).nombre_completo == "Cuenta existente"
        )
        for modelo, _ in MODELOS_Y_CANTIDADES[1:]:
            assert session.scalar(select(func.count()).select_from(modelo)) == 0
