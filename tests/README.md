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

- `integration/test_api.py` conserva las regresiones HTTP de negocio con PostgreSQL y migraciones, incluyendo la preparación de usuarios autenticados. Cada caso tiene su propio schema y verifica contrato HTTP, CRUD, reglas y persistencia. Solo se configura la dependencia de sesión para apuntar a la BD de prueba; servicios y repositorios son reales.
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

Las pruebas de este bloque se adaptan a la autenticación integrada desde `main`, incluida la renovación y recuperación del commit `83d3b94`.

- `unit/test_security.py` verifica Argon2id, firma y claims de JWT, expiración, propósito, algoritmos permitidos, configuración y decisiones por rol. Usa las bibliotecas reales, sin BD ni HTTP.
- `unit/test_auth_service.py` aísla repositorios, hashing y firma para comprobar las decisiones del servicio: alta, duplicados, bloqueo temporal, emisión y logout. El reloj se fija con `monkeypatch`.
- `integration/test_auth_api.py` recorre la API real con PostgreSQL: alta sin escalamiento de privilegios, login y `/me`, errores genéricos, bloqueo persistido, JWT inválidos, diferencias 401/403 y logout. Comprueba que el refresh se almacene como hash y que logout revoque solo su sesión.
- `integration/test_auth_persistence.py` comprueba unicidad, relaciones y persistencia de revocación y consumo. Verifica que las invalidaciones de un usuario no afecten a otro.
- `unit/test_reset_tokens.py` verifica el propósito exclusivo del JWT de recuperación, sus claims obligatorios, versión e identificadores, y los límites de la nueva contraseña.
- `integration/test_auth_flujos.py` conserva las once regresiones incorporadas por Simón, adaptadas a PostgreSQL con Alembic y al capturador SMTP compartido. Incluye reutilización, revocación, recuperación y solicitudes simultáneas. Se clasifican como integración porque usan `TestClient`.
- `integration/test_refresh_reset.py` verifica la caducidad máxima de la familia, expiración persistida, logout después de rotar, versiones de sesión, destinatario del restablecimiento y conservación de otras cuentas y sesiones.

Las fixtures de `tests/conftest.py` establecen un secreto y duraciones exclusivas de pruebas antes de cada caso y restauran el entorno al terminar. Se usa `ACCESS_TOKEN_EXPIRE_SECONDS=900` para los casos generales y `PASSWORD_RESET_EXPIRE_SECONDS=900`; la regresión del valor predeterminado comprueba explícitamente 30 segundos. `tests/security_support.py` contiene únicamente datos ficticios y utilidades para construir condiciones reproducibles. Las cuentas ADMIN/VETERINARIO se preparan por repositorio en la BD aislada; el registro público sigue creando ENTRENADOR.

`tests/smtp_capture.py` reutiliza el capturador incorporado por Simón y recibe mensajes reales por TCP/SMTP en un puerto libre de `127.0.0.1`. Las fixtures redirigen el envío a ese puerto, sin usar credenciales reales ni reenviar mensajes. El JWT se extrae del correo recibido. Servidor, hilo, mensajes y variables se limpian al finalizar; no hace falta un servicio de correo externo para estas pruebas de integración.

Los rechazos de JWT se comprueban partiendo de una sesión que primero permite `/auth/me`. Luego se cambia la condición evaluada, para no confundir un rechazo criptográfico con una familia inexistente. Las caducidades se preparan con fechas y estados de prueba; no se espera manualmente a que venza un token.

Comandos para ejecutar la parte de seguridad:

```powershell
python -m pytest tests/unit/test_security.py tests/unit/test_auth_service.py -m unit -v
python -m pytest tests/integration/test_auth_api.py tests/integration/test_auth_persistence.py -m integration -v
python -m pytest tests/unit/test_reset_tokens.py -m unit -v
python -m pytest tests/integration/test_auth_flujos.py tests/integration/test_refresh_reset.py -m integration -v
```

La suite cubre las operaciones reales `/auth/refresh`, `/auth/forgot-password` y `/auth/reset-password`: rotación y rechazo de reutilización, revocación de la familia, solicitud genérica y límites persistentes, entrega del enlace por SMTP, rechazo de JWT inválidos, nueva contraseña Argon2, consumo único e invalidación de permisos y sesiones anteriores. También comprueba que un ID ajeno enviado en la solicitud no cambie la cuenta objetivo y que las sesiones de otra cuenta sigan funcionando.

Los casos con `TestClient` se clasifican como integración. Los E2E externos se ejecutan en el nivel siguiente.

## Ejecutar los tres E2E por HTTP externo

Con PostgreSQL de pruebas iniciado:

```powershell
python -m pytest tests/e2e -m e2e -v --junitxml=tests/reports/e2e.xml
```

| Escenario | Recorrido y comprobaciones |
|---|---|
| Acceso y negocio | Registro, login, creación y consulta de entrenador/Pokémon, rechazo de asignación repetida, renovación, logout y renovación posterior rechazada. |
| Recuperación | Solicitud, recepción por SMTP, apertura del enlace real, restablecimiento, segundo uso y contraseña anterior rechazados, sesiones previas invalidadas y login con la nueva clave. |
| Permisos | La misma creación de centro devuelve 401 sin credencial, 403 con ENTRENADOR y 201 con ADMIN; la consulta confirma un único centro persistido. |

`e2e/conftest.py` arranca una instancia de Uvicorn en otro proceso para cada caso. `e2e/run_api.py` carga `app.main:app` y usa las dependencias normales de la aplicación. HTTPX realiza peticiones por TCP a `127.0.0.1`; los puertos HTTP y SMTP se asignan automáticamente.

La API se conecta mediante `DATABASE_URL` y `PGOPTIONS` al schema aislado, preparado con Alembic y vacío al comenzar cada caso. El secreto JWT, las duraciones y el correo usan configuración exclusiva de pruebas. Para el escenario de permisos, la fixture prepara únicamente la cuenta ADMIN con repositorio y Argon2 reales; la cuenta ENTRENADOR se registra por HTTP.

El enlace del mensaje SMTP apunta al puerto real de esa API. El test verifica el destinatario, extrae el JWT del fragmento y abre el formulario antes de restablecer. No requiere iniciar manualmente otra API ni otro servicio de correo.

Al finalizar, el cliente cierra sus conexiones, el proceso de Uvicorn recibe la señal de cierre por su entrada estándar, el capturador SMTP termina y se limpian los datos. `tests/reports/e2e/` conserva logs técnicos y JSON con PID de la API, PID del lanzador, puerto y código de salida. Los logs de acceso HTTP están desactivados y esa carpeta queda excluida de Git. Si la API no inicia o no cierra correctamente, la prueba falla.

El comando general `python -m pytest tests` incluye los tres niveles. La medición y el refuerzo de cobertura mínima del 85% corresponden al bloque 5.

Las dependencias versionadas y los comandos del README principal/CI corresponden a sus responsables; esta suite requiere `pytest` y usará `pytest-cov` para los reportes de cobertura.
