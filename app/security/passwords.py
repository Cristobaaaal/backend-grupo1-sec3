from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Genera un hash Argon2 de la contraseña."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Comprueba si la contraseña coincide con el hash."""
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError, VerificationError):
        return False