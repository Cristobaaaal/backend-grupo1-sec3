import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt


ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 15


def _obtener_clave() -> str:
    clave = os.getenv("JWT_SECRET_KEY")

    if not clave or len(clave.encode("utf-8")) < 32:
        raise RuntimeError(
            "Configura JWT_SECRET_KEY con al menos 32 bytes."
        )

    return clave


def crear_access_token(usuario_id: UUID) -> str:
    ahora = datetime.now(timezone.utc)

    contenido = {
        "sub": str(usuario_id),
        "iat": ahora,
        "exp": ahora + timedelta(minutes=ACCESS_TOKEN_MINUTES),
        "jti": str(uuid4()),
        "type": "access",
    }

    return jwt.encode(
        contenido,
        _obtener_clave(),
        algorithm=ALGORITHM,
    )


def decodificar_access_token(token: str) -> dict:
    contenido = jwt.decode(
        token,
        _obtener_clave(),
        algorithms=[ALGORITHM],
        options={
            "require": ["sub", "iat", "exp", "jti", "type"],
        },
    )

    if contenido["type"] != "access":
        raise jwt.InvalidTokenError("Tipo de token incorrecto.")

    try:
        UUID(contenido["sub"])
    except (ValueError, TypeError, AttributeError) as exc:
        raise jwt.InvalidTokenError(
            "Identificador de usuario inválido."
        ) from exc

    return contenido