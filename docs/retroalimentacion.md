# Matriz de Retroalimentación y Seguimiento (Entregas I y II → Entrega III)

En cumplimiento del punto 5.2 de la pauta de la Entrega Final (ICINF1108 · Desarrollo de Backend), este documento registra la evaluación oficial recibida en la entrega unificada de **Entregas I y II** (informe de revisión del docente: **29/30 · Nota 6.8**) junto con las observaciones recibidas durante la presentación oral, detallando las acciones aplicadas, la evidencia en el repositorio y el estado real de cada punto.

---

## 1. Matriz de Observaciones Recibidas

| ID / Observación recibida | Origen | Cambio y evidencia | Comprobación / Estado |
|---|---|---|---|
| **R-01 · Falta de evidencia de resultados en pruebas iniciales.** En el punto 10 de la revisión E1+E2 se indicó: *"Cumplen en parte (2/3). Hay nueve pruebas automatizadas y 27 bloques en la colección `.http`, sin evidencia del resultado obtenido en ninguna de las dos."* | Revisión escrita E1+E2 (Docente) | Se agregaron pruebas automatizadas en `tests/unit` (67), `tests/integration` (62, con PostgreSQL y migraciones) y `tests/e2e` (3 escenarios contra la API en ejecución), con cobertura mínima de 85% y reportes en `tests/reports/` (`junit.xml`, `coverage.xml`, HTML). El pipeline de GitHub Actions ejecuta ruff, el formato y las pruebas en cada PR y en `main`, y solo publica la imagen si pasan. Archivos: `tests/`, `tests/run_checks.py`, `.github/workflows/docker-publish.yml`. PR #41 (`8012462`) y PR #42 (`05d0977`). | **Resuelta**. Verificado con `python tests/run_checks.py --level all` (cobertura de 91,77% informada en el PR #41) y con las ejecuciones `quality-and-tests` en verde en la pestaña Actions. |
| **R-02 · Migrar la base de datos de SQLite a PostgreSQL.** Pasar de SQLite en archivo local a PostgreSQL con almacenamiento persistente. | Defensa oral E1+E2 (Docente) | Se incorporó `psycopg2-binary` en `pyproject.toml` y `uv.lock`; se adaptó `app/infrastructure/database.py` para conectarse a PostgreSQL sin parámetros exclusivos de SQLite; se configuró `postgres:16-alpine` con volumen persistente `postgres_data` en `docker-compose.yml` y `.env.example`. Commits: `7da07a7`, `dc0006e`, `5814197` (PR #35 y PR #37). | **Resuelta**. Verificado en `main`: la API conecta con PostgreSQL y conserva los datos en el volumen `postgres_data` al recrear el contenedor. |
| **R-03 · Dockerizar la solución completa con visor visual de base de datos.** Contenerizar la API, PostgreSQL y un servicio visual para inspeccionar la base de datos. | Defensa oral E1+E2 (Docente) | Se agregaron `Dockerfile`, `.dockerignore` y `docker-compose.yml` separando `api`, `postgres` (con `healthcheck`), `pgadmin` (visor visual en puerto `5050` con volumen `pgadmin_data`) y `mailpit` (capturador de correo para pruebas). La API ejecuta `alembic upgrade head` y el seeder idempotente al iniciar. Commits: `7da07a7`, `e519800`, `0afe150`, `9ec1a31`, `9d42faf`, `0192c8d` (PR #35 y PR #37). | **Resuelta**. Verificado con `docker compose up -d --build`: arranque ordenado (`condition: service_healthy`), Swagger operativo en `:8000/docs` y pgAdmin operativo en `:5050`. |
| **R-04 · Incorporar un `Makefile` para comandos frecuentes.** Facilitar la ejecución reproducible de comandos durante el desarrollo y la defensa para evitar olvidos en vivo. | Defensa oral E1+E2 (Docente) | Se agregó `Makefile` en la raíz del repositorio con objetivos para instalación (`install`), migraciones (`migrate`), seeder (`seed`), ejecución local (`run`), pruebas (`test`) y operación Docker (`up`, `down`, `restart`, `logs`, `ps`). Archivo: `Makefile`. | **Resuelta**. Objetivos verificados y listos para uso en desarrollo y presentación. |
| **R-05 · Mejorar la presentación (diapositivas) y preparación de la defensa.** Corregir estructura, claridad y diseño del material de apoyo para la exposición. | Defensa oral E1+E2 (Docente) | Se planificó el rediseño completo del material de apoyo (máximo 15 diapositivas legibles con el orden recomendado en la sección 8 de la pauta) y ensayos cronometrados de 10 minutos con todos los integrantes operando la API. | **Pendiente**. Corresponde al Hito 5 (cierre previo a la defensa final y etiqueta `v1.0`). |

---

## 2. Resumen de Cumplimiento Previo (Informe Oficial Entregas I y II · 29/30 · Nota 6.8)

Los siguientes criterios fueron aprobados íntegramente (3/3) en la entrega anterior y se mantienen operativos de forma acumulativa en la Entrega III (sección 5.1):

| Criterio E1+E2 | Puntaje | Estado y continuidad en Entrega III |
|---|---|---|
| 1. Ejecución y endpoints (29 rutas en 4 recursos) | 3/3 | **Mantenido**. Se conservan los 4 recursos y todas sus rutas de negocio. |
| 2. Modelo del dominio (4 entidades, 1:N, diagramas) | 3/3 | **Mantenido y ampliado**. Se sumaron `Usuario`, `RefreshToken` y `PasswordResetToken` y se actualizaron los diagramas en `docs/diagramas.md` (PR #36). |
| 3. REST, DTO y OpenAPI | 3/3 | **Mantenido y ampliado**. OpenAPI documenta las rutas de autenticación y recuperación, el esquema Bearer y las respuestas 401 y 403 (PR #39 y PR #40). |
| 4. CRUD y persistencia SQLAlchemy | 3/3 | **Mantenido y migrado a PostgreSQL** (PR #37). |
| 5. Validaciones (6 tipos) y reglas de negocio | 3/3 | **Mantenido** sin regresiones. |
| 6. Respuestas y errores HTTP uniformes | 3/3 | **Mantenido**. |
| 7. Filtro, orden y paginación en `pokemones` | 3/3 | **Mantenido**. |
| 8. Arquitectura por capas | 3/3 | **Mantenido**. |
| 9. Migraciones Alembic y seeder idempotente | 3/3 | **Mantenido y ampliado**. Migración `b71d8e12a45c` encadenada y seeder con 3 cuentas demo por rol (PR #36). |
| 10. Pruebas iniciales | 2/3 | **Subsanado (ver R-01)**. Pruebas unitarias, de integración y E2E con reportes y cobertura ≥85%, ejecutadas automáticamente en CI (PR #41 y PR #42). |
