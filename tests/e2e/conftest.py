"""API real en proceso separado, PostgreSQL migrado y capturador SMTP por caso."""

import json
import os
import subprocess
import sys
import time
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.models import RolUsuario, Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.security.passwords import hash_password
from tests.database import PROJECT_ROOT
from tests.security_support import TEST_PASSWORD, TEST_SECURITY_ENV
from tests.smtp_capture import smtp_capture


def esperar_api(proceso, estado, log):
    """Espera disponibilidad HTTP con límite; un fallo del proceso no se omite."""
    limite = time.monotonic() + 25
    while time.monotonic() < limite:
        if proceso.poll() is not None:
            raise RuntimeError(f"La API terminó antes de iniciar. Revisa {log}")
        try:
            datos = json.loads(estado.read_text(encoding="utf-8"))
            # En Windows, el lanzador del venv puede ejecutar otro intérprete hijo.
            if datos["pid"] == os.getpid():
                raise RuntimeError(
                    "La API debe ejecutarse fuera del proceso de pytest."
                )
            base_url = f"http://127.0.0.1:{datos['port']}"
            with httpx.Client(
                base_url=base_url, trust_env=False, timeout=0.5
            ) as client:
                if client.get("/").status_code == 200:
                    return base_url
        except (OSError, ValueError, httpx.TransportError):
            pass
        time.sleep(0.05)
    raise RuntimeError(f"La API no estuvo disponible en 25 segundos. Revisa {log}")


def detener_api(proceso):
    """Solicita cierre normal para liberar conexiones; limita la espera del hijo."""
    if proceso.stdin is not None and not proceso.stdin.closed:
        proceso.stdin.close()
    try:
        return proceso.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proceso.terminate()
        try:
            proceso.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proceso.kill()
            proceso.wait(timeout=5)
        raise RuntimeError("La API de pruebas no respondió al cierre normal.") from None


@pytest.fixture
def e2e_app(clean_database, request):
    """Arranca Uvicorn sin overrides de dependencias y usa HTTPX por TCP real."""
    reportes = PROJECT_ROOT / "tests" / "reports" / "e2e"
    reportes.mkdir(parents=True, exist_ok=True)
    nombre = uuid4().hex
    estado = reportes / f"api-{nombre}.json"
    log = reportes / f"api-{nombre}.log"
    with clean_database.connect() as connection:
        schema = connection.scalar(text("SELECT current_schema()"))

    with smtp_capture() as smtp:
        entorno = os.environ.copy()
        entorno.update(TEST_SECURITY_ENV)
        entorno.update(
            {
                "DATABASE_URL": clean_database.url.render_as_string(
                    hide_password=False
                ),
                "PGOPTIONS": f"-csearch_path={schema}",
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPATH": str(PROJECT_ROOT),
                "SMTP_HOST": "127.0.0.1",
                "SMTP_PORT": str(smtp.server_address[1]),
                "SMTP_FROM": "no-reply@pokemon.local",
                "SMTP_STARTTLS": "false",
                "SMTP_USER": "",
                "SMTP_PASSWORD": "",
            }
        )
        comando = [sys.executable, "-m", "tests.e2e.run_api", str(estado)]
        if request.config.getoption(
            "cov_source", default=None
        ) and not request.config.getoption("no_cov", default=False):
            # pytest-cov combina los archivos paralelos al cerrar la sesión.
            # La API debe medir sus propias peticiones en el proceso hijo.
            from coverage import Coverage

            medicion = Coverage.current()
            assert medicion is not None
            entorno["COVERAGE_FILE"] = str(PROJECT_ROOT / medicion.config.data_file)
            comando = [
                sys.executable,
                "-m",
                "coverage",
                "run",
                "--parallel-mode",
                "--context=e2e-api",
            ]
            if medicion.config.config_file:
                comando.extend(
                    ["--rcfile", str(PROJECT_ROOT / medicion.config.config_file)]
                )
            if medicion.config.source:
                comando.extend(["--source", ",".join(medicion.config.source)])
            if medicion.config.branch:
                comando.append("--branch")
            comando.extend(["-m", "tests.e2e.run_api", str(estado)])
        with log.open("wb") as salida:
            proceso = subprocess.Popen(
                comando,
                cwd=PROJECT_ROOT,
                env=entorno,
                stdin=subprocess.PIPE,
                stdout=salida,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            try:
                base_url = esperar_api(proceso, estado, log)
                datos = json.loads(estado.read_text(encoding="utf-8"))
                assert datos["pid"] != os.getpid()
                with httpx.Client(
                    base_url=base_url, trust_env=False, timeout=10
                ) as client:
                    yield SimpleNamespace(
                        client=client,
                        smtp=smtp,
                        base_url=base_url,
                        pid=datos["pid"],
                    )
            finally:
                codigo = detener_api(proceso)
                if estado.exists():
                    datos = json.loads(estado.read_text(encoding="utf-8"))
                    datos["launcher_pid"] = proceso.pid
                    datos["exit_code"] = codigo
                    estado.write_text(json.dumps(datos), encoding="utf-8")
                if codigo != 0:
                    raise RuntimeError(
                        f"La API terminó con código {codigo}. Revisa {log}"
                    )


@pytest.fixture
def cuenta_admin(clean_database):
    """Prepara el perfil autorizado con persistencia y Argon2 reales, antes del flujo."""
    with Session(clean_database) as session:
        return UsuarioRepository(session).crear(
            Usuario(
                id=uuid4(),
                email="admin-e2e@example.com",
                nombre_completo="Admin E2E",
                password_hash=hash_password(TEST_PASSWORD),
                rol=RolUsuario.ADMIN,
            )
        )
