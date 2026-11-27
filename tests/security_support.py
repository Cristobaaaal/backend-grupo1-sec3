"""Datos exclusivos de pruebas; no usar estas credenciales en despliegues."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

TEST_PASSWORD = "ClaveDePruebas123!"
TEST_JWT_SECRET = "0123456789abcdef" * 4
TEST_SECURITY_ENV = {
    "JWT_SECRET": TEST_JWT_SECRET,
    "JWT_ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_SECONDS": "900",
    "PASSWORD_RESET_EXPIRE_SECONDS": "900",
}


def access_payload(**cambios):
    """Fabrica claims vigentes; los negativos cambian solo la condición evaluada."""
    ahora = datetime.now(UTC)
    datos = {
        "sub": str(UUID(int=1)),
        "iat": ahora - timedelta(seconds=1),
        "exp": ahora + timedelta(minutes=5),
        "jti": str(uuid4()),
        "type": "access",
        "ver": 0,
        "sid": str(UUID(int=8)),
    }
    datos.update(cambios)
    return datos


def alterar_firma(token):
    """Modifica el inicio de la firma sin alterar la estructura del JWT."""
    cabecera, contenido, firma = token.split(".")
    firma = ("A" if firma[0] != "A" else "B") + firma[1:]
    return f"{cabecera}.{contenido}.{firma}"
