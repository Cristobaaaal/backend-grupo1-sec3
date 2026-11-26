"""Ejecuta un nivel de pruebas y genera evidencia sin instalar herramientas."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--level", choices=("unit", "integration", "e2e", "all"), default="all"
    )
    args = parser.parse_args()
    reportes = PROJECT_ROOT / "tests" / "reports" / args.level
    reportes.mkdir(parents=True, exist_ok=True)
    cache = reportes / "pytest-cache"
    cache.mkdir(exist_ok=True)
    entorno = os.environ.copy()
    entorno["PYTHONDONTWRITEBYTECODE"] = "1"
    entorno["COVERAGE_FILE"] = str(reportes / ".coverage")
    seleccion = (
        ["tests"] if args.level == "all" else [f"tests/{args.level}", "-m", args.level]
    )
    comando = [
        sys.executable,
        "-m",
        "pytest",
        *seleccion,
        "-o",
        f"cache_dir={cache}",
        "--cov",
        "--cov-config=tests/.coveragerc",
        "--cov-context=test",
        "--cov-report=term-missing",
        f"--cov-report=xml:{reportes / 'coverage.xml'}",
        f"--cov-report=json:{reportes / 'coverage.json'}",
        f"--cov-report=html:{reportes / 'html'}",
        f"--junitxml={reportes / 'junit.xml'}",
    ]
    # Un nivel aislado no pretende cubrir toda app. El 85% se exige en "all".
    if args.level != "all":
        comando.append("--cov-fail-under=0")
    return subprocess.call(comando, cwd=PROJECT_ROOT, env=entorno)


if __name__ == "__main__":
    raise SystemExit(main())
