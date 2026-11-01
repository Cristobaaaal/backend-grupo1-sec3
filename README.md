# API Pokémon

API REST para gestionar entrenadores, Pokémon, centros Pokémon y registros médicos. Usa FastAPI, Pydantic, SQLAlchemy, SQLite y Alembic. Proyecto de Desarrollo de Backend (ICINF1108).

## Integrantes

| Integrante | Área principal |
|---|---|
| [Benjamín Pedraza](https://github.com/bpedrazav) | Integración, OpenAPI y documentación |
| [Cristóbal Dapellus](https://github.com/Cristobaaaal) | Servicios, reglas de negocio y endpoints |
| [Franco Lillo](https://github.com/francou-ops) | Dominio, repositorios y persistencia |
| [Simón Millaguir](https://github.com/smillanguir2026-cloud) | Pruebas y datos de demostración |

## Puesta en marcha desde una copia limpia

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

   uv crea automáticamente el entorno virtual `.venv` e instala las versiones registradas en `uv.lock`, comprobando que coincidan con `pyproject.toml`. No necesitas activar el entorno: `uv run` ejecuta los comandos dentro de él. Para este procedimiento no se utiliza `requirements.txt`.

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
Cliente → Router FastAPI → DTO Pydantic → Servicio → Repositorio SQLAlchemy → SQLite
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
├── services/         # Casos de uso y reglas de negocio
├── tests_manual/     # Peticiones HTTP reproducibles
└── main.py           # Aplicación FastAPI
migrations/           # Migraciones Alembic
docs/diagramas.md     # Diagramas Mermaid
~~~

## Modelo y reglas principales

Un entrenador puede tener muchos Pokémon; cada Pokémon puede estar sin entrenador o tener uno. Un Pokémon y un centro pueden aparecer en muchos registros médicos; cada registro médico pertenece a un único Pokémon y a un único centro. Las claves foráneas están definidas en los modelos ORM y SQLite las aplica en las conexiones de la API.

- La asignación exige que el Pokémon no tenga entrenador; la transferencia exige un entrenador diferente.
- Un entrenador con Pokémon asociados no se puede eliminar.
- Un Pokémon con registros médicos no se puede eliminar.
- El centro debe existir y estar en servicio para registrar atención. La fecha de ingreso no puede estar en el futuro.
- No se puede eliminar un centro con pacientes en tratamiento ni con registros médicos históricos.

## Contrato HTTP

Hay 28 operaciones de las cuatro entidades, más GET / de bienvenida. Swagger muestra parámetros, ejemplos y códigos de respuesta.

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
| 404 | Recurso inexistente |
| 409 | Conflicto con relaciones existentes |
| 422 | Parámetro o cuerpo inválido |

## Pruebas

Ejecuta las pruebas automatizadas desde la raíz del repositorio con uv:

~~~bash
uv run python -m unittest discover -s tests -v
~~~

Las pruebas crean una base SQLite temporal por caso, preparan sus tablas y activan las claves foráneas. Al terminar eliminan esa base; no modifican pokemon.db. No es necesario iniciar Uvicorn ni ejecutar el seeder para estas pruebas: TestClient ejecuta la aplicación y cada caso crea sus propios datos.

La colección manual está en [app/tests_manual/pruebas.http](app/tests_manual/pruebas.http) y puede abrirse con REST Client en VS Code. La preparación de la base y el seeder descritos arriba permiten reproducir las peticiones sobre datos conocidos. La evidencia y los casos de prueba finales se preparan por separado.
