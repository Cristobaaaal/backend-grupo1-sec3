.PHONY: help install run migrate seed lint format format-check test test-unit test-integration test-e2e test-db test-db-down check up down restart logs ps

help:
	@echo "Comandos disponibles:"
	@echo "  make install           - Instala dependencias (incluye pytest, pytest-cov y ruff) con uv"
	@echo "  make migrate           - Aplica las migraciones de Alembic (upgrade head)"
	@echo "  make seed              - Carga los datos de demostracion (no duplica registros)"
	@echo "  make run               - Inicia la API local en http://127.0.0.1:8000"
	@echo "  make lint              - Linter: ruff check (mismo control que el CI)"
	@echo "  make format-check      - Verifica el formato sin modificar archivos (mismo control que el CI)"
	@echo "  make format            - Aplica el formato de ruff a los archivos"
	@echo "  make test-db           - Levanta el PostgreSQL de pruebas (puerto 5433)"
	@echo "  make test-db-down      - Detiene el PostgreSQL de pruebas"
	@echo "  make test-unit         - Pruebas unitarias con reportes en tests/reports/unit"
	@echo "  make test-integration  - Pruebas de integracion (requiere make test-db)"
	@echo "  make test-e2e          - Pruebas E2E contra la API en ejecucion (requiere make test-db)"
	@echo "  make test              - Conjunto completo con cobertura minima de 85% (requiere make test-db)"
	@echo "  make check             - lint + format-check + test, igual que el job quality-and-tests"
	@echo "  make up                - Construye y levanta API, PostgreSQL, pgAdmin y Mailpit"
	@echo "  make down              - Detiene los contenedores (conserva los volumenes)"
	@echo "  make restart           - Reinicia los contenedores"
	@echo "  make logs              - Muestra los logs de la API en tiempo real"
	@echo "  make ps                - Lista el estado de los contenedores"

install:
	uv sync --locked

migrate:
	uv run alembic upgrade head

seed:
	uv run python -m app.infrastructure.seeders.seed

run:
	uv run uvicorn app.main:app --reload

lint:
	uv run ruff check .

format-check:
	uv run ruff format --check .

format:
	uv run ruff format .

test-db:
	docker compose -f tests/docker-compose.test.yml up -d --wait

test-db-down:
	docker compose -f tests/docker-compose.test.yml down

test-unit:
	uv run python tests/run_checks.py --level unit

test-integration:
	uv run python tests/run_checks.py --level integration

test-e2e:
	uv run python tests/run_checks.py --level e2e

test:
	uv run python tests/run_checks.py --level all

check: lint format-check test

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
