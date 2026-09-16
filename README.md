# Backend Pokémon API - FastAPI

API REST desarrollada con **FastAPI** para la gestión de Entrenadores, Pokémones, Centros Pokémon y Registros Médicos. El proyecto sigue los principios de **Clean Architecture** (Arquitectura Limpia) dividido en capas (*Domain, Repository, Service, Router*).

---

## Arquitectura del Proyecto

El código está estructurado en módulos para mantener la separación de responsabilidades:

backend-grupo1-sec3/
├── app/
│   ├── core/           # Excepciones globales (APIException) y handlers
│   ├── domain/         # Modelos de entidad del dominio
│   ├── repositories/   # Persistencia en memoria
│   ├── routers/        # Endpoints de la API (Controllers)
│   ├── schemas/        # Validaciones de entrada y salida (Pydantic)
│   ├── services/       # Reglas de negocio
│   └── main.py         # Punto de entrada de la aplicación FastAPI
├── requirements.txt    # Dependencias del proyecto
└── README.md           # Documentación del proyecto

---

## Instalación y Configuración Local

### Prerrequisitos
* Python 3.10 o superior instalado.

### 1. Clonar el repositorio

git clone https://github.com/Cristobaaaal/backend-grupo1-sec3
cd backend-grupo1-sec3

### 2. Crear y activar el entorno virtual

* **Windows:**
  python -m venv venv
  venv\Scripts\activate

* **Linux / macOS:**
  python3 -m venv venv
  source venv/bin/activate

### 3. Instalar dependencias

pip install -r requirements.txt

### 4. Ejecutar la aplicación

uvicorn app.main:app --reload