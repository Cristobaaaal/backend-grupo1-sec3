from fastapi import Depends
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.repositories.centro_pokemon_repository import CentroPokemonRepository
from app.repositories.pokemon_repository import PokemonRepository
from app.repositories.registro_medico_repository import RegistroMedicoRepository
from app.repositories.trainer_repository import EntrenadorRepository
from app.services.centro_pokemon_service import CentroPokemonService
from app.services.pokemon_service import PokemonService
from app.services.registro_medico_service import RegistroMedicoService
from app.services.trainer_service import EntrenadorService


def get_trainer_service(db: Session = Depends(get_db)) -> EntrenadorService:
    return EntrenadorService(
        EntrenadorRepository(db),
        PokemonRepository(db),
    )


def get_pokemon_service(db: Session = Depends(get_db)) -> PokemonService:
    return PokemonService(
        PokemonRepository(db),
        EntrenadorRepository(db),
        RegistroMedicoRepository(db),
    )


def get_centro_service(db: Session = Depends(get_db)) -> CentroPokemonService:
    return CentroPokemonService(
        CentroPokemonRepository(db),
        RegistroMedicoRepository(db),
    )


def get_registro_service(db: Session = Depends(get_db)) -> RegistroMedicoService:
    return RegistroMedicoService(
        RegistroMedicoRepository(db),
        PokemonRepository(db),
        CentroPokemonRepository(db),
    )
 