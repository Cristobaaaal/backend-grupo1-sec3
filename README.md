# API Pokémon

API REST para gestionar entrenadores, Pokémon, centros Pokémon y registros médicos. Usa FastAPI, Pydantic, SQLAlchemy, PostgreSQL y Alembic. Proyecto de Desarrollo de Backend (ICINF1108).

Versión desplegada: https://pokemones.inf.uct.cl (Swagger en https://pokemones.inf.uct.cl/docs).

## Integrantes

- [Benjamín Pedraza](https://github.com/bpedrazav)
- [Cristóbal Dapellus](https://github.com/Cristobaaaal)
- [Felipe Cheuque](https://github.com/fcheuque)
- [Franco Lillo](https://github.com/francou-ops)
- [Simón Millanguir](https://github.com/smillanguir2026-cloud)

## Ejecución con Docker

Levanta la API, PostgreSQL, pgAdmin (visor de la base) y Mailpit (correo de prueba). Se requiere Docker con Docker Compose. Las variables de ejemplo están en [.env.example](.env.example), sin credenciales reales; cópialo a `.env` para cambiarlas. El archivo `.env` no se sube al repositorio ni entra en la imagen.

| Acción | Comando |
|---|---|
| Construir e iniciar | `docker compose up -d --build` |
| Ver estado | `docker compose ps` |
| Detener (conserva los datos) | `docker compose down` |
| Ver logs | `docker compose logs -f api` |
| Aplicar migraciones | `docker compose exec api alembic upgrade head` |
| Ejecutar seeders | `docker compose exec api python -m app.infrastructure.seeders.seed` |

Al iniciar, la API aplica las migraciones y ejecuta el seeder automáticamente. Los datos se guardan en el volumen `postgres_data` y sobreviven a recrear la API; `docker compose down -v` borra también los volúmenes. Servicios: API en http://localhost:8000/docs, pgAdmin en http://localhost:5050 y Mailpit en http://127.0.0.1:8025. Si el puerto 5432 está ocupado, inicia con `POSTGRES_PORT=5433 docker compose up -d --build`.

### Cuentas de demostración

El seeder crea una cuenta por rol: `admin@pokemon.com` (`ADMIN`), `veterinario@pokemon.com` (`VETERINARIO`) y `entrenador@pokemon.com` (`ENTRENADOR`). Solo guarda el hash Argon2id de cada contraseña; las contraseñas no están en el repositorio y se entregan por el canal privado del equipo y del docente. El registro público (`POST /auth/register`) siempre crea cuentas `ENTRENADOR`.

## Puesta en marcha local (sin Docker)

Se requiere Python 3.13 o superior y uv instalado. Comprueba que está disponible con `uv --version`. Ejecuta todos los comandos desde la raíz del repositorio.

1. Clona el repositorio y entra al directorio:

   ~~~powershell
   git clone https://github.com/Cristobaaaal/backend-grupo1-sec3.git
   cd backend-grupo1-sec3
   ~~~

2. Prepara el entorno e instala las dependencias con uv. El comando es el mismo en Windows, Linux y macOS:

   ~~~bash
   uv sync --locked
   ~~~

   uv crea automáticamente el entorno virtual `.venv` e instala las versiones registradas en `uv.lock`, comprobando que coincidan con `pyproject.toml`. No necesitas activar el entorno: `uv run` ejecuta los comandos dentro de él. También instala las herramientas de desarrollo (`pytest`, `pytest-cov` y `ruff`).

3. Copia la configuración de ejemplo si quieres definir explícitamente la ruta de la base de datos. Si omites este paso, la API usa igualmente el archivo local pokemon.db:

   ~~~powershell
   Copy-Item .env.example .env
   ~~~

   En Linux/macOS usa: cp .env.example .env. La variable DATABASE_URL admite la URL de SQLite; el valor de ejemplo es sqlite:///./pokemon.db. El archivo .env se carga al iniciar la aplicación. No incluyas datos privados en el repositorio.

4. Crea las tablas con la migración y carga los datos de demostración:

   ~~~powershell
   uv run alembic upgrade head
   uv run python -m app.infrastructure.seeders.seed
   ~~~

   El seeder agrega dos entrenadores, dos Pokémon, dos centros y dos registros médicos. Si lo ejecutas otra vez, omite los ID ya existentes.

5. Inicia el servidor:

   ~~~powershell
   uv run uvicorn app.main:app --reload
   ~~~

La API queda en http://127.0.0.1:8000 y la interfaz interactiva en http://127.0.0.1:8000/docs. El contrato OpenAPI también está en http://127.0.0.1:8000/openapi.json. Para usar otra ruta de SQLite, configura DATABASE_URL antes de ejecutar la migración y el servidor; ambos deben apuntar a la misma base.

## Problema que resuelve

La API centraliza el registro de Pokémon y sus entrenadores, permite asignar o transferir su responsable y mantiene la atención médica asociada a centros. Las reglas de negocio evitan, entre otros casos, asignar un Pokémon que ya tiene entrenador, registrar atención en un centro fuera de servicio y eliminar recursos que todavía tienen relaciones que deben conservarse.

## Arquitectura

Cada petición sigue este recorrido:

~~~text
Cliente → Router FastAPI → DTO Pydantic → Servicio → Repositorio SQLAlchemy → PostgreSQL
                ↓             ↓              ↓
            Depends       validación      modelo de dominio / mapper
                ↓
          sesión por petición
~~~

El router recibe HTTP y declara el contrato; el DTO valida entrada y salida; el servicio ejecuta las reglas; el repositorio guarda y consulta las entidades; el mapper convierte entre modelos de dominio y ORM. FastAPI crea y cierra una sesión de base de datos por petición mediante Depends. Alembic administra el esquema.

Los [diagramas de clases, datos y flujo de peticiones](docs/diagramas.md) muestran las relaciones y las capas con más detalle.

~~~text
app/
├── core/             # Dependencias, excepciones y manejadores de errores
├── domain/           # Entidades y enumeraciones del dominio
├── infrastructure/   # Conexión, modelos ORM, mappers y seeder
├── repositories/     # Consultas y persistencia SQLAlchemy
├── routers/          # Rutas HTTP
├── schemas/          # DTO y validaciones Pydantic
├── security/         # Hash Argon2, JWT, permisos por rol y envío de correo
├── services/         # Casos de uso y reglas de negocio
├── tests_manual/     # Peticiones HTTP reproducibles
└── main.py           # Aplicación FastAPI
migrations/           # Migraciones Alembic
tests/                # Pruebas unitarias, de integración y E2E
docs/                 # Diagramas y matriz de retroalimentación
.github/workflows/    # CI, publicación de la imagen y despliegue
~~~

### Separación de la autenticación

| Responsabilidad | Archivo |
|---|---|
| Transporte HTTP: rutas `/auth/*`, cuerpos y códigos de respuesta | `app/routers/auth_router.py` |
| Lectura del Bearer y obtención del usuario actual (401) | `app/core/dependencies.py` |
| Permisos por rol (403) | `app/security/permissions.py` |
| Casos de uso: registro, login, bloqueo, refresh, logout y recuperación | `app/services/auth_service.py` |
| Generación y validación de JWT (firma, algoritmo, `exp`, `sub`, propósito) | `app/security/tokens.py` |
| Hash y verificación de contraseñas (Argon2id) | `app/security/passwords.py` |
| Envío del correo de recuperación | `app/security/mail.py` |
| Persistencia de sesiones, refresh y tokens de recuperación | `app/repositories/token_repository.py` |

## Modelo y reglas principales

Un entrenador puede tener muchos Pokémon; cada Pokémon puede estar sin entrenador o tener uno. Un Pokémon y un centro pueden aparecer en muchos registros médicos; cada registro médico pertenece a un único Pokémon y a un único centro. Las claves foráneas están definidas en los modelos ORM y la base de datos las aplica.

- La asignación exige que el Pokémon no tenga entrenador; la transferencia exige un entrenador diferente.
- Un entrenador con Pokémon asociados no se puede eliminar.
- Un Pokémon con registros médicos no se puede eliminar.
- El centro debe existir y estar en servicio para registrar atención. La fecha de ingreso no puede estar en el futuro.
- No se puede eliminar un centro con pacientes en tratamiento ni con registros médicos históricos.

## Contrato HTTP

Hay 28 operaciones de las cuatro entidades, más GET / de bienvenida. Swagger muestra parámetros, ejemplos y códigos de respuesta.

Rutas públicas: `GET /` y `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/forgot-password` y `/auth/reset-password`. Todas las rutas de negocio y `/auth/me` exigen un access token Bearer. Crear y actualizar centros requiere rol `ADMIN` o `VETERINARIO`, y eliminar un centro es exclusivo de `ADMIN`.

### Entrenadores

| Método | Ruta | Acción |
|---|---|---|
| POST | /entrenadores/ | Crear |
| GET | /entrenadores/ | Listar |
| GET | /entrenadores/{entrenador_id} | Obtener por ID |
| PUT | /entrenadores/{entrenador_id} | Reemplazar datos |
| DELETE | /entrenadores/{entrenador_id} | Eliminar |

### Pokémon

| Método | Ruta | Acción |
|---|---|---|
| POST | /pokemones/ | Crear |
| GET | /pokemones/ | Listar con filtro, orden y paginación |
| GET | /pokemones/sin-entrenador | Listar sin entrenador |
| GET | /pokemones/tipo/{tipo} | Listar por tipo |
| GET | /pokemones/{pokemon_id} | Obtener por ID |
| GET | /pokemones/entrenador/{entrenador_id} | Listar por entrenador |
| PUT | /pokemones/{pokemon_id} | Reemplazar datos |
| DELETE | /pokemones/{pokemon_id} | Eliminar |
| PATCH | /pokemones/{pokemon_id}/asignar/{entrenador_id} | Asignar entrenador |
| PATCH | /pokemones/{pokemon_id}/transferir/{nuevo_entrenador_id} | Transferir |
| PATCH | /pokemones/{pokemon_id}/liberar | Liberar |
| PATCH | /pokemones/{pokemon_id}/stats | Cambiar nivel y puntos de vida |

El listado acepta tipo (FUEGO, AGUA, PLANTA o ELECTRICO), ordenar_por (nombre, nivel o puntos_vida), direccion (asc o desc), pagina (desde 1) y limite (1 a 100). Por ejemplo:

~~~text
GET /pokemones/?tipo=ELECTRICO&ordenar_por=nivel&direccion=desc&pagina=1&limite=20
~~~

La respuesta incluye items, total, pagina, limite y total_paginas.

### Centros Pokémon

| Método | Ruta | Acción |
|---|---|---|
| POST | /centros-pokemon/ | Crear |
| GET | /centros-pokemon/ | Listar |
| GET | /centros-pokemon/ciudad/{ciudad} | Buscar por ciudad |
| GET | /centros-pokemon/{centro_id} | Obtener por ID |
| PUT | /centros-pokemon/{centro_id} | Reemplazar datos |
| DELETE | /centros-pokemon/{centro_id} | Eliminar |

### Registros médicos

| Método | Ruta | Acción |
|---|---|---|
| POST | /registros-medicos/ | Crear |
| GET | /registros-medicos/ | Listar |
| GET | /registros-medicos/{registro_id} | Obtener por ID |
| PUT | /registros-medicos/{registro_id} | Reemplazar datos |
| DELETE | /registros-medicos/{registro_id} | Eliminar |

## Errores

Los errores controlados tienen una estructura común:

~~~json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "No existe el recurso solicitado",
    "details": []
  }
}
~~~

| HTTP | Significado |
|---|---|
| 400 | Regla de negocio incumplida |
| 401 | Token ausente, inválido, vencido o revocado, o credenciales incorrectas |
| 403 | Usuario autenticado sin permiso para la operación |
| 404 | Recurso inexistente |
| 409 | Conflicto con relaciones existentes o correo ya registrado |
| 422 | Parámetro o cuerpo inválido |
| 429 | Demasiados intentos de restablecimiento |

## Pruebas

Las pruebas están en `tests/unit` (67), `tests/integration` (62) y `tests/e2e` (3 escenarios). Integración y E2E usan un PostgreSQL de pruebas separado, preparado con las migraciones de Alembic; las unitarias no lo necesitan. El detalle de cada archivo está en [tests/README.md](tests/README.md).

Desde la raíz del repositorio, con las dependencias instaladas (`uv sync --locked`):

~~~bash
docker compose -f tests/docker-compose.test.yml up -d --wait
uv run python tests/run_checks.py --level all
~~~

| Nivel | Comando |
|---|---|
| Unitarias | `uv run python tests/run_checks.py --level unit` |
| Integración | `uv run python tests/run_checks.py --level integration` |
| E2E | `uv run python tests/run_checks.py --level e2e` |
| Conjunto completo (exige cobertura ≥85%) | `uv run python tests/run_checks.py --level all` |

Los reportes quedan en `tests/reports/<nivel>/`: `junit.xml` (cantidad de pruebas aprobadas y fallidas), `coverage.xml`, `coverage.json` y `html/index.html` (cobertura por archivo). Esa carpeta no se sube al repositorio. Si una prueba falla o la cobertura queda bajo 85%, el comando termina con error.

Condiciones de los datos de prueba: cada caso usa un schema nuevo en la base `pokemon_test` (puerto 5433), migrado con Alembic y eliminado al terminar; nunca se usan datos reales. El correo se captura con un servidor SMTP local y los tiempos de expiración se preparan sin esperar que venzan los tokens. Para detener la base de pruebas: `docker compose -f tests/docker-compose.test.yml down`.

Linter y formateador (ruff), los mismos que ejecuta el CI:

~~~bash
uv run ruff check .
uv run ruff format --check .
~~~

La colección manual está en [app/tests_manual/pruebas.http](app/tests_manual/pruebas.http) y puede abrirse con REST Client en VS Code. La preparación de la base y el seeder descritos arriba permiten reproducir las peticiones sobre datos conocidos. La evidencia y los casos de prueba finales se preparan por separado.

## Autenticación y recuperación

Después de actualizar el código aplica `uv run alembic upgrade head`. La migración
`c92ef03a6d10` agrega familias de sesión, una versión de credenciales y límites
persistentes. Conserva usuarios y datos de negocio, pero revoca los refresh
anteriores sin familia. Los access anteriores tampoco son válidos: inicia sesión nuevamente.

Configura una clave JWT local, sin subirla a Git. Puedes generar una con:

~~~powershell
uv run python -c "import secrets; print(secrets.token_urlsafe(48))"
~~~

Copia el resultado a `JWT_SECRET` en tu `.env`. Las variables actuales son:

| Variable | Valor de ejemplo | Uso |
|---|---|---|
| JWT_ALGORITHM | HS256 | Algoritmo permitido: HS256, HS384 o HS512 |
| ACCESS_TOKEN_EXPIRE_SECONDS | 30 | Caducidad del access token en segundos |
| PASSWORD_RESET_EXPIRE_SECONDS | 900 | Caducidad del JWT de recuperación |
| PASSWORD_RESET_URL | http://127.0.0.1:8000/auth/reset-password | Dirección del formulario incluido |
| SMTP_HOST | mailpit | Host desde Docker; usar 127.0.0.1 si la API corre fuera de Docker |
| SMTP_PORT | 1025 | Puerto SMTP de prueba |
| SMTP_FROM | no-reply@pokemon.local | Remitente del correo |

`ACCESS_TOKEN_EXPIRE_MINUTES` ya no se utiliza. Los refresh mantienen una sesión
máxima de siete días; rotarlos no prolonga esa fecha. Reiniciar el servidor conserva
sesiones, revocaciones y límites en la base de datos.

| Método | Ruta | Resultado |
|---|---|---|
| POST | /auth/register | Crea ENTRENADOR; contraseña de 12 a 128 caracteres |
| POST | /auth/login | Devuelve access y refresh; cinco fallos bloquean 15 minutos |
| GET | /auth/me | Datos públicos del usuario; requiere Bearer |
| POST | /auth/refresh | Consume refresh y entrega un nuevo par |
| POST | /auth/logout | Revoca toda la sesión, access y refresh; devuelve 204 |
| POST | /auth/forgot-password | Recibe email y devuelve siempre el mismo 202 |
| POST | /auth/reset-password | Recibe token y password; cambia la contraseña |

Reutilizar un refresh consumido revoca toda su familia, incluidos sus access y los
refresh descendientes, sin cerrar las otras sesiones del usuario. Cambiar la contraseña
incrementa la versión del usuario y revoca todas sus sesiones y permisos de recuperación
anteriores en una sola transacción. El JWT de recuperación usa `type=password_reset`;
no sirve como access token ni viceversa.

Para comprobarlo en Swagger: haz login, usa el refresh una vez y vuelve a enviar el
anterior. La segunda petición debe dar 401 y los tokens de esa familia dejan de funcionar.
Después de logout tampoco se permite renovar. Un access válido deja de funcionar al
cumplir los 30 segundos; solicita uno nuevo con un refresh vigente.

### Correo con Mailpit

Con Docker Compose:

~~~bash
docker compose up -d --build
~~~

Mailpit queda en http://127.0.0.1:8025. Si ejecutas la API con uv en el equipo, puedes
iniciar solo `docker compose up -d mailpit` y usar `SMTP_HOST=127.0.0.1` en `.env`;
el puerto SMTP 1025 está publicado solo en localhost.

Envía `POST /auth/forgot-password` con el correo de una cuenta existente. Abre el
mensaje en Mailpit y sigue su enlace al formulario. El token se transporta en el
fragmento del enlace para no incluirlo en los logs HTTP. La respuesta no revela si la
cuenta existe; si SMTP falla, se registra un error operativo sin mostrar tokens.

Límites persistentes, por ventanas fijas de 15 minutos: tres solicitudes por correo,
veinte por IP y veinte confirmaciones por IP. Las solicitudes limitadas conservan el
202 genérico sin enviar más correos; las confirmaciones limitadas devuelven 429. No se
confía en `X-Forwarded-For`: al desplegar detrás de un proxy, configura las IP de proxy
confiables en Uvicorn para identificar correctamente al cliente. Las filas históricas
de `auth_rate_limits` pueden purgarse durante mantenimiento si ya no se necesitan.

Los casos de `tests/integration/test_auth_flujos.py` usan una base de pruebas y un receptor SMTP local:
no envían correos externos. Cubren rotación, reutilización, logout, recuperación,
expiración, propósito, límites y consumo concurrente. El puerto dinámico del receptor
se cierra al terminar.

## Integración continua (CI/CD)

El pipeline está en [.github/workflows/docker-publish.yml](.github/workflows/docker-publish.yml) y se ejecuta al abrir o actualizar un pull request hacia `main`, al integrar cambios en `main` y al crear un tag `v*`.

1. **`quality-and-tests`**: instala las dependencias con uv, ejecuta `ruff check` y `ruff format --check`, levanta el PostgreSQL de pruebas y corre las pruebas de los tres niveles con cobertura mínima de 85%. Cualquier error detiene el pipeline.
2. **`publicar`**: solo se ejecuta si el paso anterior pasa, y solo en `main` o en un tag (no en pull requests). Construye la imagen para `linux/amd64` y la publica en GitHub Container Registry con las etiquetas `latest` y `sha-<commit>`:

   ~~~text
   ghcr.io/cristobaaaal/backend-grupo1-sec3:latest
   ghcr.io/cristobaaaal/backend-grupo1-sec3:sha-<commit>
   ~~~

3. **Despliegue** ([.github/workflows/deploy.yml](.github/workflows/deploy.yml)): cuando la publicación termina con éxito en `main`, reinicia la app en Kubero para que descargue la imagen nueva. Usa el token `KUBERO_TOKEN`, guardado como secreto del repositorio en GitHub.

Así, a Kubero solo llega una revisión que pasó el linter, el formato y las pruebas. Los resultados de cada ejecución se ven en la pestaña **Actions** del repositorio.

## Despliegue en Kubero UCT

| Dato | Valor |
|---|---|
| URL | https://pokemones.inf.uct.cl (HTTPS; HTTP redirige a HTTPS) |
| Aplicación en Kubero | pipeline `pokemones`, fase `production`, app `pokemones` |
| Imagen | `ghcr.io/cristobaaaal/backend-grupo1-sec3:latest` |
| Base de datos | Complemento PostgreSQL de Kubero, con almacenamiento persistente |

**Configuración.** Las variables se definen en Kubero, en la configuración de la app, nunca en el repositorio: `DATABASE_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_SECONDS`, `PASSWORD_RESET_URL` y `PASSWORD_RESET_EXPIRE_SECONDS`.

**Migraciones y datos.** Al iniciar, la imagen ejecuta `alembic upgrade head`, que solo aplica las migraciones pendientes y no borra tablas ni datos. Los datos se guardan en el PostgreSQL del complemento, por lo que sobreviven a los reinicios de la API. El seeder no se ejecuta automáticamente en Kubero; para cargar las cuentas de demostración se ejecuta una vez desde la consola de la app: `python -m app.infrastructure.seeders.seed` (no duplica registros).

**Trazabilidad.** Cada imagen publicada tiene la etiqueta `sha-<commit>`, y `latest` apunta a la última revisión de `main` aprobada por el CI. El commit desplegado se identifica en la pestaña Actions (ejecución de "Deploy to Kubero") y en GitHub Packages, donde `latest` aparece junto a su etiqueta `sha-<commit>`.

**Logs y salud.** Los logs de la API se ven en Kubero, en la pestaña **Registros** de la app, y no incluyen contraseñas ni tokens. La disponibilidad se comprueba con `GET /`, que responde `{"message": "Welcome to the Pokemón Medical Center API!"}`, y en el mapa de la app de Kubero, que muestra el estado del pod.

**Reversión.** Para volver a una versión anterior, en la configuración de la app en Kubero se cambia la etiqueta de la imagen de `latest` a la `sha-<commit>` de esa versión y se guarda. Si la versión nueva agregó una migración, la imagen anterior no la conoce y falla al iniciar, porque Alembic no encuentra la revisión registrada en la base. En ese caso, antes de cambiar la imagen hay que deshacer esa migración con la versión actual (`alembic downgrade <revisión anterior>`), lo que elimina las tablas o columnas que ella agregó.

**Limitaciones.**
- El correo de recuperación no está configurado en Kubero (no hay servidor SMTP de prueba). La API responde igual, pero el correo no se envía; el flujo completo se demuestra en local con Mailpit.
- El access token dura 30 segundos, configurable con `ACCESS_TOKEN_EXPIRE_SECONDS`.
- Detrás del proxy de Kubero, los límites por IP de la recuperación pueden ver la IP del proxy en lugar de la del cliente.
- Durante un redespliegue la API puede responder 502 unos segundos.

## Retroalimentación

Las observaciones recibidas en las Entregas I y II, los cambios aplicados, sus commits y su estado están en [docs/retroalimentacion.md](docs/retroalimentacion.md).
