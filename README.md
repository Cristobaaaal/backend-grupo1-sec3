# Backend Pokémon API - FastAPI

API REST desarrollada con **FastAPI** para la gestión de Entrenadores, Pokémones, Centros Pokémon y Registros Médicos. El proyecto sigue los principios de **Clean Architecture** (Arquitectura Limpia) dividido en capas (*Domain, Repository, Service, Router*).

Proyecto grupal del ramo **Desarrollo de Backend (ICINF1108)**.

---

## Integrantes y responsabilidades

| Integrante | Responsabilidad principal |
|---|---|
| [Benjamín Pedraza](https://github.com/bpedrazav) | Coordinación y seguimiento + Documentación e integración (organización del backlog, README, Swagger/OpenAPI) |
| [Cristobal Dapellus](https://github.com/Cristobaaaal) | API y lógica de negocio (implementación de endpoints, servicios, manejo de errores) |
| [Franco Lillo](https://github.com/francou-ops) | Dominio y datos (modelado de entidades, relaciones, DTO, validaciones) |
| Simon Millaguir(https://github.com/smillanguir2026-cloud) | Calidad y pruebas (verificación funcional de endpoints, colección de pruebas manuales) |

Todos los integrantes comprenden el funcionamiento completo de la API y participaron en su desarrollo, pruebas e integración.

---

## Arquitectura del Proyecto

El código está estructurado en módulos para mantener la separación de responsabilidades:

```
backend-grupo1-sec3/
├── app/
│   ├── core/           # Excepciones globales (APIException), handlers y repos compartidos (dependencies.py)
│   ├── domain/         # Modelos de entidad del dominio
│   ├── repositories/   # Persistencia en memoria
│   ├── routers/        # Endpoints de la API (Controllers)
│   ├── schemas/        # Validaciones de entrada y salida (Pydantic)
│   ├── services/       # Reglas de negocio
│   ├── tests_manual/   # Colección de pruebas manuales (.http)
│   └── main.py         # Punto de entrada de la aplicación FastAPI
├── requirements.txt    # Dependencias del proyecto
└── README.md           # Documentación del proyecto
```

---

## Instalación y Configuración Local

### Prerrequisitos
* Python 3.10 o superior instalado.

### 1. Clonar el repositorio

```
git clone https://github.com/Cristobaaaal/backend-grupo1-sec3
cd backend-grupo1-sec3
```

### 2. Crear y activar el entorno virtual

* **Windows:**
  ```
  python -m venv venv
  venv\Scripts\activate
  ```

* **Linux / macOS:**
  ```
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Instalar dependencias

```
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación

```
uvicorn app.main:app --reload
```

La API queda disponible en `http://127.0.0.1:8000`.

---

## Documentación interactiva (Swagger/OpenAPI)

Con el servidor corriendo, la documentación interactiva generada automáticamente está disponible en:

**http://127.0.0.1:8000/docs**

Ahí se puede ver el detalle completo de cada endpoint (parámetros, ejemplos de entrada/salida, respuestas posibles) y ejecutar peticiones de prueba directamente desde el navegador.

---

## Pruebas manuales

La colección de pruebas manuales está en `app/tests_manual/pruebas.http`. Contiene requests para las 4 entidades, incluyendo casos exitosos y casos de error (404, 422, y las reglas de negocio). Se puede ejecutar directamente en VS Code con la extensión **REST Client**, o usar cada request como referencia para reproducirla en Postman/Thunder Client.

---

## Manejo de errores

Todos los errores controlados por la API devuelven la misma estructura JSON:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "No existe un pokemon con el ID ...",
    "details": []
  }
}
```

| Situación | HTTP | `code` |
|---|---|---|
| Recurso no existe | 404 | `RESOURCE_NOT_FOUND` |
| Viola regla de negocio | 400 | `BUSINESS_RULE_VIOLATION` |
| Conflicto | 409 | `RESOURCE_CONFLICT` |
| Falla validación de datos | 422 | `VALIDATION_ERROR` |

---

## Contrato de Endpoints

### Entrenadores (`/entrenadores`)

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/entrenadores/` | Crear entrenador |
| GET | `/entrenadores/` | Listar entrenadores |
| GET | `/entrenadores/{entrenador_id}` | Obtener entrenador por ID |
| PUT | `/entrenadores/{entrenador_id}` | Actualizar entrenador |
| DELETE | `/entrenadores/{entrenador_id}` | Eliminar entrenador |

### Pokémones (`/pokemones`)

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/pokemones/` | Crear pokémon (valida que `entrenador_id` exista, si viene) |
| GET | `/pokemones/` | Listar pokémones — soporta filtro (`tipo`), orden (`ordenar_por`, `direccion`) y paginación (`pagina`, `limite`) |
| GET | `/pokemones/sin-entrenador` | Listar pokémones sin entrenador asignado |
| GET | `/pokemones/tipo/{tipo}` | Listar pokémones por tipo |
| GET | `/pokemones/{pokemon_id}` | Obtener pokémon por ID |
| GET | `/pokemones/entrenador/{entrenador_id}` | Listar pokémones de un entrenador |
| PUT | `/pokemones/{pokemon_id}` | Actualizar pokémon |
| DELETE | `/pokemones/{pokemon_id}` | Eliminar pokémon |
| PATCH | `/pokemones/{pokemon_id}/asignar/{entrenador_id}` | Asignar entrenador a un pokémon sin entrenador |
| PATCH | `/pokemones/{pokemon_id}/transferir/{nuevo_entrenador_id}` | Transferir pokémon a otro entrenador |
| PATCH | `/pokemones/{pokemon_id}/liberar` | Liberar pokémon (queda sin entrenador) |
| PATCH | `/pokemones/{pokemon_id}/stats` | Actualizar nivel y puntos de vida |

### Centros Pokémon (`/centros-pokemon`)

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/centros-pokemon/` | Crear centro pokémon |
| GET | `/centros-pokemon/` | Listar centros |
| GET | `/centros-pokemon/ciudad/{ciudad}` | Listar centros por ciudad |
| GET | `/centros-pokemon/{centro_id}` | Obtener centro por ID |
| PUT | `/centros-pokemon/{centro_id}` | Actualizar centro |
| DELETE | `/centros-pokemon/{centro_id}` | Eliminar centro (rechaza si tiene pacientes `EN_TRATAMIENTO`) |

### Registros Médicos (`/registros-medicos`)

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/registros-medicos/` | Crear registro médico (valida que `pokemon_id` y `centro_id` existan, centro en servicio y fecha no futura) |
| GET | `/registros-medicos/` | Listar registros médicos |
| GET | `/registros-medicos/{registro_id}` | Obtener registro por ID |
| PUT | `/registros-medicos/{registro_id}` | Actualizar registro médico |
| DELETE | `/registros-medicos/{registro_id}` | Eliminar registro médico |

**Total: 28 endpoints.**
