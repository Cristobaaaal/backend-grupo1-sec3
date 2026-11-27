import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt


def _obtener_algoritmo() -> str:
    algoritmo = os.getenv("JWT_ALGORITHM", "HS256")
    if algoritmo not in {"HS256", "HS384", "HS512"}:
        raise RuntimeError("JWT_ALGORITHM debe ser HS256, HS384 o HS512.")
    return algoritmo


def _obtener_clave() -> str:
    clave = os.getenv("JWT_SECRET")
    if not clave or len(clave.encode("utf-8")) < 32:
        raise RuntimeError("Configura JWT_SECRET con al menos 32 bytes.")
    return clave


def _duracion(nombre: str, defecto: int) -> int:
    segundos = int(os.getenv(nombre, str(defecto)))
    if segundos <= 0:
        raise RuntimeError(f"{nombre} debe ser positivo.")
    return segundos


def _crear(
    usuario_id: UUID, version: int, proposito: str, segundos: int, **extra
) -> str:
    ahora = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(usuario_id),
            "iat": ahora,
            "exp": ahora + timedelta(seconds=segundos),
            "jti": str(uuid4()),
            "type": proposito,
            "ver": version,
            **extra,
        },
        _obtener_clave(),
        algorithm=_obtener_algoritmo(),
    )


def crear_access_token(usuario_id: UUID, familia_id: str, version: int) -> str:
    return _crear(
        usuario_id,
        version,
        "access",
        _duracion("ACCESS_TOKEN_EXPIRE_SECONDS", 30),
        sid=familia_id,
    )


def validar_configuracion_access() -> None:
    _obtener_clave()
    _obtener_algoritmo()
    _duracion("ACCESS_TOKEN_EXPIRE_SECONDS", 30)


def crear_reset_token(usuario_id: UUID, version: int) -> str:
    return _crear(
        usuario_id,
        version,
        "password_reset",
        _duracion("PASSWORD_RESET_EXPIRE_SECONDS", 900),
    )


def _decodificar(token: str, proposito: str) -> dict:
    requeridos = ["sub", "iat", "exp", "jti", "type", "ver"]
    if proposito == "access":
        requeridos.append("sid")
    contenido = jwt.decode(
        token,
        _obtener_clave(),
        algorithms=[_obtener_algoritmo()],
        options={"require": requeridos},
    )
    if contenido["type"] != proposito or type(contenido["ver"]) is not int:
        raise jwt.InvalidTokenError("Propósito o versión de token inválidos.")
    try:
        UUID(contenido["sub"])
        UUID(contenido["jti"])
        if proposito == "access":
            UUID(contenido["sid"])
    except (ValueError, TypeError, AttributeError) as exc:
        raise jwt.InvalidTokenError("Identificador de token inválido.") from exc
    return contenido


def decodificar_access_token(token: str) -> dict:
    return _decodificar(token, "access")


def decodificar_reset_token(token: str) -> dict:
    return _decodificar(token, "password_reset")
