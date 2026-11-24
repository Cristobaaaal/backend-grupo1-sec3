.PHONY: help install run migrate seed test up down logs restart ps

help:
	@echo "Comandos disponibles:"
	@echo "  make install  - Instala dependencias locales con uv"
	@echo "  make migrate  - Aplica las migraciones de Alembic (upgrade head)"
	@echo "  make seed     - Carga los datos iniciales de demostracion"
	@echo "  make run      - Inicia la API en modo desarrollo local (puerto 8000)"
	@echo "  make test     - Ejecuta las pruebas automatizadas con pytest"
	@echo "  make up       - Construye y levanta los contenedores (API, Postgres, pgAdmin, Mailpit)"
	@echo "  make down     - Detiene y elimina los contenedores (conserva volumenes)"
	@echo "  make restart  - Reinicia los contenedores"
	@echo "  make logs     - Muestra los logs de la API en tiempo real"
	@echo "  make ps       - Lista el estado de los contenedores"

install:
	uv sync --locked

migrate:
	uv run alembic upgrade head

seed:
	uv run python -m app.infrastructure.seeders.seed

run:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest -v

up:
	docker compose up -d --build

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f api

ps:
	docker compose ps
