from uuid import UUID
from pydantic import BaseModel, Field
from app.domain.models import TipoPokemon, EstadoAtencion
from typing import Optional
from datetime import date

class CrearEntrenador(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=50) # "..." para que el campo sea obligatorio
    nivel_experiencia: int = Field(..., ge=1, le=100) # Mayor o igual a 1, o menor o igual a 100. 
    region_origen: str = Field(..., min_length=2, max_length= 50)
    medallas_obtenidas: int = Field(default=0, ge=0, le=8)

class CrearPokemon(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=15)
    tipo_principal: TipoPokemon
    nivel: int = Field(..., ge=1, le=100)
    puntos_vida: int = Field(..., ge=1, le=100)
    entrenador_id: Optional[UUID] = None #asi deja q sea opcional al tenerlo vacio por defecto no lo pide despues
class CrearCentroPokemon(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=50)
    ciudad: str = Field(..., min_length=2, max_length=50)
    capacidad_maxima: int = Field(..., ge=1, le=100)
    en_servicio: bool = Field(default=True)

class CrearRegistroMedico(BaseModel):
    pokemon_id: UUID
    centro_id: UUID
    diagnostico: str = Field(..., min_length=2, max_length=100)
    fecha_ingreso: date
    estado: EstadoAtencion
    costo: int = Field(..., ge=0)
