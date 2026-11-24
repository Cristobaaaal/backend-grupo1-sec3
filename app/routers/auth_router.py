from fastapi import APIRouter, Depends, Response, status

from app.core.dependencies import get_auth_service, get_current_user
from app.domain.models import Usuario
from app.schemas.auth_schemas import (
    LoginRequest,
    LogoutRequest,
    RegistroRequest,
    TokenResponse,
    UsuarioResponse,
)
from app.schemas.schemas import ErrorResponse
from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"],
)


@router.post(
    "/register",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar usuario",
    description=(
        "Crea una cuenta con rol ENTRENADOR. "
        "La contraseña debe tener entre 12 y 128 caracteres. "
        "La respuesta no incluye la contraseña ni su hash."
    ),
    responses={
        409: {
            "model": ErrorResponse,
            "description": "El correo ya está registrado.",
        },
        422: {
            "model": ErrorResponse,
            "description": "Los datos enviados no son válidos.",
        },
    },
)
def registrar(
    datos: RegistroRequest,
    servicio: AuthService = Depends(get_auth_service),
):
    return servicio.registrar(datos)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    description=(
        "Valida las credenciales y devuelve un access token JWT "
        "y un refresh token. Después de cinco intentos fallidos, "
        "la cuenta queda bloqueada durante quince minutos."
    ),
    responses={
        401: {
            "model": ErrorResponse,
            "description": (
                "Credenciales inválidas, cuenta bloqueada "
                "o cuenta desactivada."
            ),
        },
        422: {
            "model": ErrorResponse,
            "description": "Los datos enviados no son válidos.",
        },
    },
)
def login(
    datos: LoginRequest,
    servicio: AuthService = Depends(get_auth_service),
):
    return servicio.login(datos)


@router.get(
    "/me",
    response_model=UsuarioResponse,
    summary="Consultar mi usuario",
    description=(
        "Devuelve los datos del usuario autenticado mediante "
        "un access token Bearer válido. "
        "No devuelve la contraseña ni su hash."
    ),
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Token inválido, vencido o ausente.",
        },
    },
)
def obtener_mi_usuario(
    usuario: Usuario = Depends(get_current_user),
):
    return usuario


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Cerrar sesión",
    description=(
        "Revoca el refresh token recibido. Repetir la solicitud "
        "devuelve igualmente 204. El access token ya emitido "
        "conserva su validez hasta su vencimiento."
    ),
    responses={
        422: {
            "model": ErrorResponse,
            "description": "Los datos enviados no son válidos.",
        },
    },
)
def logout(
    datos: LogoutRequest,
    servicio: AuthService = Depends(get_auth_service),
):
    servicio.logout(datos.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)