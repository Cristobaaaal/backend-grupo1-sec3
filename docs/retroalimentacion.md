# Matriz de Retroalimentación y Seguimiento

En cumplimiento del punto 5.2 de la pauta de evaluación de la Entrega III (ICINF1108 - Desarrollo de Backend), este documento registra las observaciones recibidas durante las entregas anteriores, las acciones correspondientes, su evidencia y el estado real de avance en el repositorio.

---

## Matriz de Observaciones y Estado

| ID | Observación Recibida | Cambio y Evidencia Aplicada | Comprobación / Estado |
|---|---|---|---|
| **R-01** | **Dockerización integral de la solución**: Se requiere dockerizar la API, PostgreSQL y un visor de base de datos sin depender de SQLite. | Se prepararon `Dockerfile`, `.dockerignore` y `docker-compose.yml`. Falta incorporar `psycopg2-binary` en las dependencias oficiales (`pyproject.toml`) y desacoplar `database.py` de parámetros exclusivos de SQLite. | **Parcial**. Estructura base de compose creada en commit `7da07a7`; pendiente integración de driver Postgres por Felipe (área CI/dependencias). |
| **R-02** | **Migración de base de datos a PostgreSQL**: Pasar de SQLite local a PostgreSQL con volúmenes persistentes. | Configurado servicio `postgres:16-alpine` con volumen `postgres_data` y variable `DATABASE_URL` en compose y `.env.example`. | **Parcial**. La infraestructura de Docker está lista, pero la conexión nativa de la app se completará con las dependencias de Postgres. |
| **R-03** | **Orden de arranque de contenedores**: La API no debe levantarse antes de que la base de datos esté lista para recibir conexiones. | Se configuró directiva `depends_on: - postgres` en compose. | **Pendiente / Parcial**. Requiere sumar un `healthcheck` en el servicio Postgres en Docker compose para que el inicio sea verdaderamente condicional al estado saludable. |
| **R-04** | **Persistencia para autenticación y seguridad**: No existían modelos de datos para usuarios, roles ni tokens. | Se crearon las entidades de dominio y modelos ORM `Usuario`, `RefreshToken` y `PasswordResetToken` con soporte de 3 roles (`ADMIN`, `VETERINARIO`, `ENTRENADOR`). Se generó la migración Alembic `b71d8e12a45c`. | **Resuelta**. Modelos en `app/domain/models.py` y `app/infrastructure/models.py`. Migración probada localmente desde copia limpia. |
| **R-05** | **Datos de prueba para perfiles de seguridad**: El seeder no contaba con usuarios para validar acceso y autorización en la defensa. | Se incorporaron 3 cuentas de demostración en `app/infrastructure/seeders/seed.py` con hashes Argon2id legítimos sin secretos expuestos en comentarios. | **Resuelta**. Seeder validado con ejecución limpia mediante `uv run python -m app.infrastructure.seeders.seed`. |
| **R-06** | **Eliminación de archivos compilados `*.pyc` en el repositorio**: Existían archivos binarios `.pyc` commiteados en el árbol de trabajo. | Se eliminaron los 17 archivos `.pyc` rastreados mediante `git rm` y se reforzó `.gitignore` y `.dockerignore`. | **Resuelta**. Comprobado con `git ls-files *.pyc` resultando vacío. |

---

## Verificación de Cumplimiento Acumulativo (Sección 5.1)

1. **Dominio y Contrato**: Se conservan intactas las 4 entidades de negocio originales (`Entrenador`, `Pokemon`, `CentroPokemon`, `RegistroMedico`) y se suman las entidades de soporte para seguridad (`Usuario`, `RefreshToken`, `PasswordResetToken`).
2. **Persistencia Real**: Se conservan las migraciones versionadas con Alembic aplicadas de forma secuencial (`4629db295117` -> `b71d8e12a45c`).
3. **Cero regresiones**: Ninguna regla de negocio existente (asignación de Pokémon, centros en servicio, eliminación restringida) ha sido alterada.
