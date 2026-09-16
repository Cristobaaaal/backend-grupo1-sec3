from fastapi import FastAPI
from app.routers.trainer_router import router as trainer_router
from app.routers.pokemon_router import router as pokemon_router
from app.routers.centro_pokemon_router import router as centro_pokemon_router
from app.routers.registro_medico_router import router as registro_medico_router
from app.core.handlers import register_exception_handlers

app = FastAPI(
    title="Pokemón Medical Center API",
    description="API for the management of trainers, Pokémon and medical centers",
    version="1.0.0"
)

register_exception_handlers(app)

app.include_router(trainer_router)
app.include_router(pokemon_router)
app.include_router(centro_pokemon_router)
app.include_router(registro_medico_router)

@app.get("/")
def bienvenida():
    return {"message": "Welcome to the Pokemón Medical Center API!"}