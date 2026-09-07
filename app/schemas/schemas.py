from pydantic import BaseModel, Field

class CrearEntrenador(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=50) # "..." para que el campo sea obligatorio
    nivel_experiencia: int = Field(..., ge=1, le=100) # Mayor o igual a 1, o menor o igual a 100. 
    region_origen: str = Field(..., min_length=2, max_length= 50)
    medallas_obtenidas: int = Field(default=0, ge=0, le=8)

class CrearPokemon(BaseModel):
    nombre: str Field(..., min_length=2, max_length=15)