from uuid import UUID
from datetime import date
from typing import Optional, List, Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field
from app.domain.models import TipoPokemon, EstadoAtencion

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "items": [{
                "id": "30000000-0000-4000-8000-000000000001",
                "nombre": "Pikachu",
                "tipo_principal": "ELECTRICO",
                "nivel": 20,
                "puntos_vida": 80,
                "entrenador_id": "10000000-0000-4000-8000-000000000001",
            }],
            "total": 1,
            "pagina": 1,
            "limite": 20,
            "total_paginas": 1,
        }]
    })
    items: List[T]
    total: int
    pagina: int
    limite: int
    total_paginas: int

class CrearEntrenador(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "nombre": "faker",
                "nivel_experiencia": 67,
                "region_origen": "corea",
                "medallas_obtenidas": 3
            }]
        }
    )
    nombre: str = Field(..., min_length=2, max_length=50) 
    nivel_experiencia: int = Field(..., ge=1, le=100) 
    region_origen: str = Field(..., min_length=2, max_length=50)
    medallas_obtenidas: int = Field(default=0, ge=0, le=8)

class CrearPokemon(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "nombre": "Pikachu",
            "tipo_principal": "ELECTRICO",
            "nivel": 20,
            "puntos_vida": 80,
            "entrenador_id": "10000000-0000-4000-8000-000000000001",
        }]
    })
    nombre: str = Field(..., min_length=2, max_length=15)
    tipo_principal: TipoPokemon
    nivel: int = Field(..., ge=1, le=100)
    puntos_vida: int = Field(..., ge=1, le=100)
    entrenador_id: Optional[UUID] = None 

class CrearCentroPokemon(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "nombre": "Centro Norte",
                "ciudad": "Temuco",
                "capacidad_maxima": 10,
                "en_servicio": True
            }]
        }
    )

    nombre: str = Field(..., min_length=2, max_length=50)
    ciudad: str = Field(..., min_length=2, max_length=50)
    capacidad_maxima: int = Field(..., ge=1, le=100)
    en_servicio: bool = Field(default=True)

class CrearRegistroMedico(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "pokemon_id": "30000000-0000-4000-8000-000000000001",
            "centro_id": "20000000-0000-4000-8000-000000000001",
            "diagnostico": "Agotamiento",
            "fecha_ingreso": "2026-01-01",
            "estado": "EN_TRATAMIENTO",
            "costo": 5000,
        }]
    })
    pokemon_id: UUID
    centro_id: UUID
    diagnostico: str = Field(..., min_length=2, max_length=100)
    fecha_ingreso: date
    estado: EstadoAtencion
    costo: int = Field(..., ge=0) # El costo debe ser mayor o igual a 0

class EntrenadorResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [{
                "id": "00000000-0000-0000-0000-000000000001",
                "nombre": "faker",
                "nivel_experiencia": 67,
                "region_origen": "corea",
                "medallas_obtenidas": 3
            }]
        }
    )

    id: UUID
    nombre: str
    nivel_experiencia: int
    region_origen: str
    medallas_obtenidas: int

class PokemonResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{
            "id": "30000000-0000-4000-8000-000000000001",
            "nombre": "Pikachu",
            "tipo_principal": "ELECTRICO",
            "nivel": 20,
            "puntos_vida": 80,
            "entrenador_id": "10000000-0000-4000-8000-000000000001",
        }]},
    )

    id: UUID
    nombre: str
    tipo_principal: TipoPokemon
    nivel: int
    puntos_vida: int
    entrenador_id: Optional[UUID]

class CentroPokemonResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [{
                "id": "00000000-0000-0000-0000-000000000002",
                "nombre": "Centro Norte",
                "ciudad": "Temuco",
                "capacidad_maxima": 10,
                "en_servicio": True
            }]
        }
    )

    id: UUID
    nombre: str
    ciudad: str
    capacidad_maxima: int
    en_servicio: bool

class RegistroMedicoResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{
            "id": "40000000-0000-4000-8000-000000000001",
            "pokemon_id": "30000000-0000-4000-8000-000000000001",
            "centro_id": "20000000-0000-4000-8000-000000000001",
            "diagnostico": "Agotamiento",
            "fecha_ingreso": "2026-01-01",
            "estado": "EN_TRATAMIENTO",
            "costo": 5000,
        }]},
    )

    id: UUID
    pokemon_id: UUID
    centro_id: UUID
    diagnostico: str
    fecha_ingreso: date
    estado: EstadoAtencion
    costo: int

class ErrorInfo(BaseModel):
    code: str
    message: str
    details: List[dict]

class ErrorResponse(BaseModel):
    error: ErrorInfo
