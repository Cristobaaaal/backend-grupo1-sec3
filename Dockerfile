# Etapa 1: Base ligera de Python con uv
FROM python:3.13-slim AS base

# Evitar que Python escriba archivos .pyc y forzar salida en tiempo real en los logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Instalar uv directamente desde su imagen oficial binaria
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copiar archivos de dependencias para aprovechar la caché de capas de Docker
COPY pyproject.toml uv.lock ./

# Instalar las dependencias en el entorno virtual
RUN uv sync --frozen --no-install-project --no-dev

# Copiar el resto del código de la aplicación
COPY . .

# Instalar el proyecto
RUN uv sync --frozen --no-dev

# Asegurar que el entorno virtual esté en el PATH
ENV PATH="/app/.venv/bin:$PATH"

# Puerto expuesto por FastAPI
EXPOSE 8000

# Aplica las migraciones pendientes y luego inicia la API.
# "alembic upgrade head" no borra datos: solo aplica lo que falta.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
