# Pruebas de la API Pokémon

La organización usa como referencia la [actividad de Student del curso](https://github.com/INF-UCT/ICINF1108-templates2026/tree/estudiantes_icinf-fastapi/tests/students), revisada en el commit `e00ff6c`: pytest, fixtures, aserciones, casos parametrizados y explicaciones en cada prueba.

## Ejecutar las unitarias

Con el entorno del proyecto activado y pytest instalado:

```powershell
python -m pytest tests/unit -m unit -v
```

Desde PowerShell también se puede usar el intérprete directamente:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit -m unit -v
```

La configuración está en `tests/pytest.ini`. Al pasar `tests` o `tests/unit`, pytest la detecta y permite importar `app` desde la raíz del proyecto.

## Cómo leer las pruebas

- `unit/conftest.py` prepara fixtures nuevas para cada caso. Los repositorios simulados respetan las firmas reales mediante `create_autospec`; una protección hace fallar cualquier intento de abrir una conexión real a BD.
- `unit/test_schemas.py` verifica entradas válidas, límites y errores de Pydantic. Los casos parametrizados tienen identificadores legibles.
- `unit/test_pokemon_service.py` comprueba asignación, transferencia, historial médico y paginación.
- Los otros archivos de servicios comprueban relaciones del entrenador, borrado de centros y admisión de pacientes. La fecha se controla con `monkeypatch`, que la restaura al terminar cada caso.
- Las aserciones comprueban resultados y errores; `assert_not_called` comprueba que una operación rechazada no solicite escrituras al repositorio.

Ejemplo de un caso puntual:

```powershell
python -m pytest tests/unit/test_pokemon_service.py::test_asignar_rechaza_pokemon_que_ya_tiene_entrenador -v
```

`test_api_integracion.py` conserva las pruebas HTTP existentes. Los bloques siguientes incorporarán integración con migraciones, autenticación, E2E externos y el reporte de cobertura mínimo del 85%. Los marcadores `integration` y `e2e` quedan registrados para esos niveles.

Las dependencias versionadas y los comandos del README principal/CI corresponden a sus responsables; esta suite requiere `pytest` y usará `pytest-cov` para los reportes de cobertura.
