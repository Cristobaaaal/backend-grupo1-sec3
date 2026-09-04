from dataclasses import dataclass
from datetime import date
from enum import Enum
from uuid import UUID

class TipoPokemon(str, Enum): #Enum para que no sea texto libre. Validación de texto permitido
    FUEGO = "FUEGO"
    AGUA = "AGUA"
    PLANTA = "PLANTA"
    ELECTRICO = "ELECTRICO"

class EstadoAtencion(str, Enum):
    EN_TRATAMIENTO = "EN_TRATAMIENTO"
    DADO_DE_ALTA = "DADO_DE_ALTA"


# --- Entidades --- 

@dataclass  #dataclass para evitar definir el constructor __init__ + los self. (Menos código) 
class Entrenador:
    id: UUID # id única, no 1, 2 etc.
    nombre: str
    nivel_experiencia: int
    region_origen: str
    medallas_obtenidas: int

@dataclass
class Pokemon:
    id: UUID
    nombre: str
    tipo_principal: TipoPokemon
    nivel: int
    puntos_vida: int
    entrenador_id: UUID

@dataclass
class CentroPokemon:
    id: UUID
    nombre: str
    ciudad: str
    capacidad_maxima: int
    en_servicio: bool

@dataclass
class RegistroMedico:
    id: UUID
    pokemon_id: UUID
    centro_id: UUID
    diagnostico: str
    fecha_ingreso: date
    estado: EstadoAtencion
    costo: int