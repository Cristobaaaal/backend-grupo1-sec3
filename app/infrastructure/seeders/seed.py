from datetime import date  # Importaciones Inicio

from app.infrastructure.database import (
    SessionLocal,  # Permite abrir una sesión para trabajar con la base de datos.
)
from app.infrastructure.models import (
    CentroPokemonORM,
    EntrenadorORM,
    PokemonORM,
    RegistroMedicoORM,
    UsuarioORM,
)  # Importaciones Fin


def insertar_si_falta(
    db, modelo, datos
):  # Comprobación antes de insertar un registro en la base de datos.
    existente = db.get(modelo, datos["id"])

    if existente is not None:
        return False

    db.add(modelo(**datos))
    return True


def ejecutar_seed():  # Variados Ejemplos de seeding de datos para la base de datos.
    entrenadores = [
        {
            "id": "10000000-0000-4000-8000-000000000001",
            "nombre": "Ash",
            "nivel_experiencia": 20,
            "region_origen": "Kanto",
            "medallas_obtenidas": 4,
        },
        {
            "id": "10000000-0000-4000-8000-000000000002",
            "nombre": "Misty",
            "nivel_experiencia": 30,
            "region_origen": "Kanto",
            "medallas_obtenidas": 6,
        },
    ]

    centros = [
        {
            "id": "20000000-0000-4000-8000-000000000001",
            "nombre": "Centro Norte",
            "ciudad": "Temuco",
            "capacidad_maxima": 10,
            "en_servicio": True,
        },
        {
            "id": "20000000-0000-4000-8000-000000000002",
            "nombre": "Centro Sur",
            "ciudad": "Valdivia",
            "capacidad_maxima": 15,
            "en_servicio": True,
        },
    ]

    pokemones = [
        {
            "id": "30000000-0000-4000-8000-000000000001",
            "nombre": "Pikachu",
            "tipo_principal": "ELECTRICO",
            "nivel": 20,
            "puntos_vida": 80,
            "entrenador_id": entrenadores[0]["id"],
        },
        {
            "id": "30000000-0000-4000-8000-000000000002",
            "nombre": "Raichu",
            "tipo_principal": "ELECTRICO",
            "nivel": 35,
            "puntos_vida": 95,
            "entrenador_id": entrenadores[0]["id"],
        },
    ]

    registros = [
        {
            "id": "40000000-0000-4000-8000-000000000001",
            "pokemon_id": pokemones[0]["id"],
            "centro_id": centros[0]["id"],
            "diagnostico": "Agotamiento",
            "fecha_ingreso": date(2026, 1, 1),
            "estado": "EN_TRATAMIENTO",
            "costo": 5000,
        },
        {
            "id": "40000000-0000-4000-8000-000000000002",
            "pokemon_id": pokemones[1]["id"],
            "centro_id": centros[1]["id"],
            "diagnostico": "Control completado",
            "fecha_ingreso": date(2026, 1, 2),
            "estado": "DADO_DE_ALTA",
            "costo": 3000,
        },
    ]

    # Usuarios de demostración para los roles requeridos en la pauta (sin secretos reales expuestos)
    # Hashes generados con Argon2id real (RFC 9106)
    usuarios = [
        {
            "id": "50000000-0000-4000-8000-000000000001",
            "email": "admin@pokemon.com",
            "password_hash": "$argon2id$v=19$m=65536,t=3,p=4$WCQgCdky1dnCw9zfjOOfEA$zCe2lbK5cpFhE7LIF/Fs9pEakLRKmWGTSRXYoGUU9so",
            "nombre_completo": "Profesor Oak (Administrador)",
            "rol": "ADMIN",
            "activo": True,
            "intentos_fallidos": 0,
            "bloqueado_hasta": None,
        },
        {
            "id": "50000000-0000-4000-8000-000000000002",
            "email": "veterinario@pokemon.com",
            "password_hash": "$argon2id$v=19$m=65536,t=3,p=4$fa0SQ9ohrYIOtMoZdp//yg$l8NnNjE6TEq92CfmgXQg6LfoClRVXbcVrGIQ/vh441U",
            "nombre_completo": "Enfermera Joy (Veterinaria)",
            "rol": "VETERINARIO",
            "activo": True,
            "intentos_fallidos": 0,
            "bloqueado_hasta": None,
        },
        {
            "id": "50000000-0000-4000-8000-000000000003",
            "email": "entrenador@pokemon.com",
            "password_hash": "$argon2id$v=19$m=65536,t=3,p=4$9FKt2GInOYZ+FkhMJSDLmg$0wg1SsMN7i+Mdt4ItZ5dRsM0byZEyhQHMyvooBnWRCI",
            "nombre_completo": "Ash Ketchum (Entrenador)",
            "rol": "ENTRENADOR",
            "activo": True,
            "intentos_fallidos": 0,
            "bloqueado_hasta": None,
        },
    ]

    grupos = [  # Grupos de datos a insertar en la base de datos
        (UsuarioORM, usuarios),
        (EntrenadorORM, entrenadores),
        (CentroPokemonORM, centros),
        (PokemonORM, pokemones),
        (RegistroMedicoORM, registros),
    ]

    creados = 0
    omitidos = 0

    with SessionLocal.begin() as db:
        for modelo, elementos in grupos:
            for datos in elementos:
                if insertar_si_falta(db, modelo, datos):
                    creados += 1
                else:
                    omitidos += 1

            # Guarda cada grupo dentro de la misma transacción.
            # Así existen los padres antes de insertar sus hijos.
            db.flush()

    print(f"Seeder completado: {creados} creados, {omitidos} existentes.")


if __name__ == "__main__":  # Arrancar Programa de Seed de Datos.
    ejecutar_seed()
