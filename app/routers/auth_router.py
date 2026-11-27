from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import HTMLResponse

from app.core.dependencies import get_auth_service, get_current_user
from app.domain.models import Usuario
from app.schemas.auth_schemas import (
    LoginRequest,
    LogoutRequest,
    MensajeResponse,
    RecuperacionRequest,
    RefreshRequest,
    RegistroRequest,
    RestablecerRequest,
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
        "de 30 segundos por defecto y un refresh token de 7 días. Después de cinco intentos fallidos, "
        "la cuenta queda bloqueada durante quince minutos."
    ),
    responses={
        401: {
            "model": ErrorResponse,
            "description": (
                "Credenciales inválidas, cuenta bloqueada o cuenta desactivada."
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
        "Revoca la familia completa del refresh recibido, incluidos sus access tokens. "
        "Repetir la solicitud devuelve igualmente 204."
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


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar la sesión con rotación de tokens",
    description=(
        "Consume un refresh vigente y devuelve nuevos access y refresh. "
        "La caducidad máxima de la sesión se conserva. Reutilizar un refresh "
        "consumido revoca toda su familia, incluidos los access tokens. "
        "Un token desconocido, vencido o posterior a logout devuelve 401."
    ),
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Refresh inválido, vencido o revocado.",
        }
    },
)
def refresh(datos: RefreshRequest, servicio: AuthService = Depends(get_auth_service)):
    return servicio.refresh(datos.refresh_token)


@router.post(
    "/forgot-password",
    response_model=MensajeResponse,
    status_code=202,
    summary="Solicitar recuperación por correo",
    description=(
        "Envía un enlace de un solo uso por SMTP/Mailpit cuando corresponde. "
        "Siempre responde el mismo 202, exista o no la cuenta. "
        "Límite persistente: 3 solicitudes por correo y 20 por IP en ventanas de 15 minutos. "
        "La respuesta también es genérica cuando se alcanza el límite. "
        "Cada nuevo enlace invalida los enlaces pendientes anteriores."
    ),
)
def solicitar_recuperacion(
    datos: RecuperacionRequest,
    request: Request,
    servicio: AuthService = Depends(get_auth_service),
):
    servicio.solicitar_recuperacion(
        str(datos.email), request.client.host if request.client else "unknown"
    )
    return MensajeResponse(
        message="Si la cuenta está disponible, recibirás instrucciones de recuperación."
    )


@router.post(
    "/reset-password",
    response_model=MensajeResponse,
    summary="Restablecer contraseña con JWT de recuperación",
    description=(
        "Requiere un JWT de propósito password_reset, vigente y no utilizado, "
        "y una contraseña de 12 a 128 caracteres. Guarda Argon2 e invalida "
        "todos los access, refresh y enlaces de recuperación anteriores en una transacción. "
        "El enlace vence a los 15 minutos por defecto."
    ),
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Token alterado, vencido, usado o de otro propósito.",
        },
        429: {
            "model": ErrorResponse,
            "description": "Más de 20 intentos por IP en 15 minutos.",
        },
        422: {"model": ErrorResponse, "description": "Contraseña o entrada inválida."},
    },
)
def restablecer(
    datos: RestablecerRequest,
    request: Request,
    servicio: AuthService = Depends(get_auth_service),
):
    servicio.restablecer(
        datos.token,
        datos.password,
        request.client.host if request.client else "unknown",
    )
    return MensajeResponse(message="Contraseña actualizada. Inicia sesión nuevamente.")


@router.get("/reset-password", response_class=HTMLResponse, include_in_schema=False)
def formulario_recuperacion():
    return HTMLResponse(
        """<!doctype html>
<html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Restablecer contraseña</title>
<body><h1>Restablecer contraseña</h1>
<form id="form"><label>Nueva contraseña (12 a 128 caracteres)
<input id="password" type="password" minlength="12" maxlength="128" required autocomplete="new-password"></label>
<button>Guardar contraseña</button></form><p id="resultado" role="status"></p>
<script>
const token = new URLSearchParams(location.hash.slice(1)).get('token');
history.replaceState(null, '', location.pathname);
document.getElementById('form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const salida = document.getElementById('resultado');
  if (!token) { salida.textContent = 'Enlace inválido.'; return; }
  try {
    const response = await fetch('/auth/reset-password', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({token, password: document.getElementById('password').value})
    });
    const data = await response.json();
    salida.textContent = response.ok ? data.message : 'No se pudo cambiar la contraseña. Solicita otro enlace o revisa los datos.';
    if (response.ok) document.getElementById('form').remove();
  } catch { salida.textContent = 'Error de conexión. Intenta nuevamente.'; }
});
</script></body></html>""",
        headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"},
    )
