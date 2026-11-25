import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt


def _obtener_algoritmo() -> str:
    algoritmo = os.getenv("JWT_ALGORITHM", "HS256")
    if algoritmo not in {"HS256", "HS384", "HS512"}:
        raise RuntimeError("JWT_ALGORITHM debe ser HS256, HS384 o HS512.")
    return algoritmo


def _obtener_duracion() -> int:
    minutos = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    if minutos <= 0:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES debe ser positivo.")
    return minutos


def _obtener_clave() -> str:
    clave = os.getenv("JWT_SECRET")

    if not clave or len(clave.encode("utf-8")) < 32:
        raise RuntimeError(
            "Configura JWT_SECRET con al menos 32 bytes."
        )

    return clave


def crear_access_token(usuario_id: UUID) -> str:
    ahora = datetime.now(timezone.utc)

    contenido = {
        "sub": str(usuario_id),
        "iat": ahora,
        "exp": ahora + timedelta(minutes=_obtener_duracion()),
        "jti": str(uuid4()),
        "type": "access",
    }

    return jwt.encode(
        contenido,
        _obtener_clave(),
        algorithm=_obtener_algoritmo(),
    )


def decodificar_access_token(token: str) -> dict:
    contenido = jwt.decode(
        token,
        _obtener_clave(),
        algorithms=[_obtener_algoritmo()],
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
