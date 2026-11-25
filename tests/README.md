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

## Ejecutar la integración con PostgreSQL

Inicia Docker Desktop y levanta la base separada de pruebas:

```powershell
docker compose -f tests/docker-compose.test.yml up -d --wait
python -m pytest tests/integration -m integration -v --junitxml=tests/reports/integration.xml
```

El contenedor usa PostgreSQL 16, escucha únicamente en `127.0.0.1:5433` y guarda datos temporales en `tmpfs`. Su proyecto Docker es `backend-grupo1-tests`; no comparte contenedores ni volúmenes con el compose de desarrollo.

La URL predeterminada es `postgresql+psycopg2://pokemon_test:pokemon_test@127.0.0.1:5433/pokemon_test`. Estas credenciales pertenecen exclusivamente al contenedor local de prueba. Para otro PostgreSQL de pruebas, configura `TEST_DATABASE_URL`; el nombre de la base debe terminar en `_test`.

`tests/database.py` crea un schema con UUID, aplica `alembic upgrade head` en un proceso separado y dirige las conexiones a ese schema. Al finalizar lo elimina. Las fixtures de pytest limpian sus tablas antes y después de cada caso, conservando `alembic_version`. No se usa `Base.metadata.create_all` ni se sustituyen los repositorios por mocks.

- `integration/test_api.py` conserva las nueve regresiones HTTP anteriores con PostgreSQL y migraciones. Cada caso tiene su propio schema y verifica contrato HTTP, CRUD, reglas y persistencia. Solo se configura la dependencia de sesión para apuntar a la BD de prueba; servicios y repositorios son reales.
- `integration/test_repositories.py` verifica revisión de Alembic, persistencia entre sesiones, claves primarias y foráneas, rollback, historial médico, orden estable de paginación y búsqueda de centros.
- `tests/conftest.py` prepara la BD y las sesiones bajo demanda. Ejecutar únicamente las pruebas unitarias no requiere iniciar PostgreSQL.

Para ejecutar el conjunto de pruebas disponible:

```powershell
python -m pytest tests --junitxml=tests/reports/all.xml
```

Los XML registran cantidades, resultados y tiempos; `tests/reports/` se excluye de Git. Las pruebas no se omiten si falta la BD: el comando falla e indica cómo iniciarla.

Para detener y retirar el contenedor de pruebas:

```powershell
docker compose -f tests/docker-compose.test.yml down
```

## Autenticación y seguridad

Las pruebas de este bloque se adaptan al código integrado desde `main` en el commit `1c1fed5`.

- `unit/test_security.py` verifica Argon2id, firma y claims de JWT, expiración, propósito, algoritmos permitidos, configuración y decisiones por rol. Usa las bibliotecas reales, sin BD ni HTTP.
- `unit/test_auth_service.py` aísla repositorios, hashing y firma para comprobar las decisiones del servicio: alta, duplicados, bloqueo temporal, emisión y logout. El reloj se fija con `monkeypatch`.
- `integration/test_auth_api.py` recorre la API real con PostgreSQL: alta sin escalamiento de privilegios, login y `/me`, errores genéricos, bloqueo persistido, JWT inválidos, diferencias 401/403 y logout. Comprueba que el refresh se almacene como hash y que logout revoque solo su sesión.
- `integration/test_auth_persistence.py` comprueba unicidad, relaciones y persistencia de revocación y consumo. Verifica que las invalidaciones de un usuario no afecten a otro.

Las fixtures de `tests/conftest.py` establecen un secreto y una duración exclusivos de pruebas antes de cada caso y restauran el entorno al terminar. `tests/security_support.py` contiene únicamente datos ficticios y utilidades para construir condiciones reproducibles. Las cuentas ADMIN/VETERINARIO se preparan por repositorio en la BD aislada; el registro público sigue creando ENTRENADOR.

Comandos para ejecutar la parte de seguridad:

```powershell
python -m pytest tests/unit/test_security.py tests/unit/test_auth_service.py -m unit -v
python -m pytest tests/integration/test_auth_api.py tests/integration/test_auth_persistence.py -m integration -v
```

### Requisitos de seguridad pendientes de implementación

En la API revisada existen `/auth/register`, `/auth/login`, `/auth/me` y `/auth/logout`. Todavía no hay rutas ni servicios de renovación o recuperación de contraseña.

Por ello, siguen pendientes la rotación del refresh y el rechazo de su reutilización, el flujo JWT de recuperación con validación y uso único, y la invalidación de access/refresh anteriores al restablecimiento. La prueba de la marca `usado` verifica persistencia: no demuestra por sí sola un flujo de recuperación ni el rechazo de un segundo uso por HTTP.

Estos casos deben incorporarse cuando estén disponibles las operaciones reales. No se registran como casos aprobados ni omitidos. Los tres flujos E2E externos y la medición de cobertura mínima del 85% también siguen pendientes. Los casos HTTP con `TestClient` se clasifican como integración.

Las dependencias versionadas y los comandos del README principal/CI corresponden a sus responsables; esta suite requiere `pytest` y usará `pytest-cov` para los reportes de cobertura.
