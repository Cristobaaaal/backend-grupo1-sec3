from fastapi import FastAPI
from app.routers.trainer_router import router as trainer_router
from app.routers.pokemon_router import router as pokemon_router
from app.routers.centro_pokemon_router import router as centro_pokemon_router
app = FastAPI(
    title="Pokemón Medical Center API",
    description="API for the management of trainers, Pokémon and medical centers",
    version="1.0.0")

app.include_router(trainer_router)
app.include_router(pokemon_router)
app.include_router(centro_pokemon_router)

@app.get("/")
def bienvenida():
    return {"message": "Welcome to the Pokemón Medical Center API!"}