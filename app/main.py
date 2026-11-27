from fastapi import Depends, FastAPI

from app.core.dependencies import get_current_user
from app.core.handlers import register_exception_handlers
from app.routers.auth_router import router as auth_router
from app.routers.centro_pokemon_router import router as centro_pokemon_router
from app.routers.pokemon_router import router as pokemon_router
from app.routers.registro_medico_router import router as registro_medico_router
from app.routers.trainer_router import router as trainer_router
from app.schemas.schemas import ErrorResponse

app = FastAPI(
    title="Pokemón Medical Center API",
    description=(
        "API para gestionar entrenadores, Pokémon y centros médicos. "
        "Las rutas de negocio requieren un access token Bearer. "
        "La gestión de centros incluye permisos por rol."
    ),
    version="1.0.0",
)

register_exception_handlers(app)


@app.middleware("http")
async def evitar_cache_autenticacion(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/auth/"):
        response.headers["Cache-Control"] = "no-store"
    return response


errores_autenticacion = {
    401: {
        "model": ErrorResponse,
        "description": "Token inválido, vencido o ausente.",
    },
}

# Registro y login deben poder utilizarse sin un access token.
# /auth/me declara su propia protección.
app.include_router(auth_router)

app.include_router(
    trainer_router,
    dependencies=[Depends(get_current_user)],
    responses=errores_autenticacion,
)

app.include_router(
    pokemon_router,
    dependencies=[Depends(get_current_user)],
    responses=errores_autenticacion,
)

# Este router ya contiene autenticación y permisos por rol.
app.include_router(centro_pokemon_router)

app.include_router(
    registro_medico_router,
    dependencies=[Depends(get_current_user)],
    responses=errores_autenticacion,
)


@app.get(
    "/",
    summary="Bienvenida",
    description=(
        "Confirma que la API está activa y devuelve un mensaje de bienvenida."
    ),
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "message": ("Welcome to the Pokemón Medical Center API!")
                    }
                }
            }
        }
    },
)
def bienvenida():
    return {"message": "Welcome to the Pokemón Medical Center API!"}
