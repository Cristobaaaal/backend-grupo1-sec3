# Matriz de Retroalimentación y Seguimiento

En cumplimiento del punto 5.2 de la pauta de evaluación de la Entrega III (ICINF1108 - Desarrollo de Backend), este documento registra de manera formal y verificable las observaciones recibidas durante las Entregas I y II, las acciones correctivas aplicadas, la evidencia en el repositorio (archivos/commits) y su comprobación técnica.

---

## Matriz de Observaciones y Estado

| ID | Observación Recibida | Cambio y Evidencia Aplicada | Comprobación / Estado |
|---|---|---|---|
| **R-01** | **Dockerización incompleta**: Faltaba dockerizar la solución completa (API, base de datos persistente y visor de administración). | Se creó `Dockerfile` optimizado con `uv`, `.dockerignore` y `docker-compose.yml` orquestando `api` (FastAPI), `postgres` (PostgreSQL 16) con volumen persistente (`postgres_data`) y `pgadmin` (pgAdmin 4). Archivos: `Dockerfile`, `docker-compose.yml`. Commits: `7da07a7`, `dc0006e`. | **Resuelta**. Verificado con `docker compose up -d`. La API y pgAdmin levantan en puertos 8000 y 5050 respectivamente. |
| **R-02** | **Migración de base de datos a PostgreSQL**: Se requería pasar de persistencia exclusiva en SQLite local a PostgreSQL como motor principal de producción y contenedores. | Se configuró `DATABASE_URL` con driver PostgreSQL (`postgresql+psycopg2://...`) por defecto en `.env.example` y `docker-compose.yml`. Se mantuvo compatibilidad dual (Postgres en producción/Docker, SQLite para ejecución local rápida). Archivos: `docker-compose.yml`, `.env.example`, `app/infrastructure/database.py`. | **Resuelta**. Verificado en composición de contenedores con volúmenes persistentes. |
| **R-03** | **Orden de inicio de servicios en Docker**: La API no debía levantarse antes de que la base de datos estuviera lista. | Se incorporó directiva `depends_on: - postgres` en el servicio `api` del `docker-compose.yml`. Archivo: `docker-compose.yml`. Commit: `dc0006e`. | **Resuelta**. Comprobado con arranque orquestado de contenedores en Docker Compose. |
| **R-04** | **Falta de modelo de usuarios y persistencia de seguridad**: No existían entidades para autenticación, roles ni sesiones en base de datos. | Se crearon las entidades de dominio y modelos ORM `Usuario`, `RefreshToken` y `PasswordResetToken` con soporte de roles (`ADMIN`, `VETERINARIO`, `ENTRENADOR`), bloqueo por intentos fallidos y revocación. Archivos: `app/domain/models.py`, `app/infrastructure/models.py`. | **Resuelta**. Migración Alembic `b71d8e12a45c` ejecutada con éxito. |
| **R-05** | **Datos iniciales de demostración para seguridad**: El seeder no contaba con cuentas de prueba para verificar roles y permisos en la defensa. | Se incorporaron 3 cuentas de prueba en el seeder oficial (`admin@pokemon.com`, `veterinario@pokemon.com`, `entrenador@pokemon.com`) utilizando hashes Argon2id sin exponer secretos reales. Archivo: `app/infrastructure/seeders/seed.py`. | **Resuelta**. Ejecución exitosa de `python -m app.infrastructure.seeders.seed` insertando usuarios demo. |
| **R-06** | **Archivos compilados `*.pyc` en el repositorio Git**: Existían artefactos compilados en caché commiteados en el árbol de trabajo. | Se agregaron patrones a `.dockerignore` y `.gitignore` para prevenir la inclusión de directorios `__pycache__` y archivos binarios de compilación. | **Resuelta**. Limpieza verificada en el control de versiones. |

---

## Verificación de Cumplimiento Acumulativo (Sección 5.1)

1. **Dominio y Contrato**: Se mantienen intactas las 4 entidades de negocio originales (`Entrenador`, `Pokemon`, `CentroPokemon`, `RegistroMedico`) y se suman las entidades de soporte para seguridad (`Usuario`, `RefreshToken`, `PasswordResetToken`).
2. **Persistencia Real**: Se conservan las migraciones versionadas con Alembic aplicadas de forma secuencial (`4629db295117` -> `b71d8e12a45c`).
3. **Cero regresiones**: Ninguna regla de negocio existente (asignación de Pokémon, centros en servicio, eliminación restringida) ha sido alterada.
