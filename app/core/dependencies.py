from datetime import UTC, datetime
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.domain.models import Usuario
from app.infrastructure.database import get_db
from app.repositories.centro_pokemon_repository import CentroPokemonRepository
from app.repositories.pokemon_repository import PokemonRepository
from app.repositories.registro_medico_repository import RegistroMedicoRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.trainer_repository import EntrenadorRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.security.tokens import decodificar_access_token
from app.services.auth_service import AuthService
from app.services.centro_pokemon_service import CentroPokemonService
from app.services.pokemon_service import PokemonService
from app.services.registro_medico_service import RegistroMedicoService
from app.services.trainer_service import EntrenadorService

bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Access token obtenido mediante POST /auth/login.",
)


def get_trainer_service(
    db: Session = Depends(get_db),
) -> EntrenadorService:
    return EntrenadorService(
        EntrenadorRepository(db),
        PokemonRepository(db),
    )


def get_pokemon_service(
    db: Session = Depends(get_db),
) -> PokemonService:
    return PokemonService(
        PokemonRepository(db),
        EntrenadorRepository(db),
        RegistroMedicoRepository(db),
    )


def get_centro_service(
    db: Session = Depends(get_db),
) -> CentroPokemonService:
    return CentroPokemonService(
        CentroPokemonRepository(db),
        RegistroMedicoRepository(db),
    )


def get_registro_service(
    db: Session = Depends(get_db),
) -> RegistroMedicoService:
    return RegistroMedicoService(
        RegistroMedicoRepository(db),
        PokemonRepository(db),
        CentroPokemonRepository(db),
    )


def get_auth_service(
    db: Session = Depends(get_db),
) -> AuthService:
    return AuthService(
        usuario_repo=UsuarioRepository(db),
        token_repo=TokenRepository(db),
    )


def get_current_user(
    credenciales: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Valida el access token y obtiene al usuario activo."""
    error = HTTPException(
        status_code=401,
        detail="Token inválido, vencido o ausente.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credenciales is None:
        raise error

    try:
        contenido = decodificar_access_token(credenciales.credentials)
        usuario_id = UUID(contenido["sub"])
    except jwt.InvalidTokenError:
        raise error from None

    usuario = UsuarioRepository(db).obtener_por_id(usuario_id)

    if (
        usuario is None
        or not usuario.activo
        or usuario.token_version != contenido["ver"]
        or not TokenRepository(db).sesion_vigente(
            contenido["sid"],
            usuario_id,
            datetime.now(UTC).replace(tzinfo=None),
        )
    ):
        raise error

    return usuario
