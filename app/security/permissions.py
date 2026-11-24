from fastapi import Depends, HTTPException

from app.core.dependencies import get_current_user
from app.domain.models import RolUsuario, Usuario


def require_roles(*roles_permitidos: RolUsuario):
    """Construye una dependencia que comprueba el rol del usuario."""

    def comprobar_rol(
        usuario: Usuario = Depends(get_current_user),
    ) -> Usuario:
        if usuario.rol not in roles_permitidos:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para realizar esta operación.",
            )

        return usuario

    return comprobar_rol