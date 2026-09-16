from uuid import UUID
from typing import List
from app.domain.models import RegistroMedico
from app.schemas.schemas import CrearRegistroMedico
from app.repositories.registro_medico_repository import RegistroMedicoRepository
from datetime import date
from app.repositories.pokemon_repository import PokemonRepository
from app.repositories.centro_pokemon_repository import CentroPokemonRepository
from app.core.exceptions import NotFoundException, BusinessRuleError

class RegistroMedicoService:
    def __init__(
        self,
        repository: RegistroMedicoRepository,
        pokemon_repository: PokemonRepository,
        centro_repository: CentroPokemonRepository,
    ):
        self.repository = repository
        self.pokemon_repository = pokemon_repository
        self.centro_repository = centro_repository

    def _validar_datos(self, datos: CrearRegistroMedico) -> None:
        if not self.pokemon_repository.get_by_id(datos.pokemon_id):
            raise NotFoundException("pokemon", datos.pokemon_id)
        centro = self.centro_repository.get_by_id(datos.centro_id)
        if not centro:
            raise NotFoundException("centro pokémon", datos.centro_id)
        if not centro.en_servicio:
            raise BusinessRuleError(
                f"el centro {datos.centro_id} no esta en servicio, no puede recibir pacientes."
            )
        if datos.fecha_ingreso > date.today():
            raise BusinessRuleError("la fecha de ingreso no puede ser una fecha futura.")
        
    def crear_registro(self, datos: CrearRegistroMedico) -> RegistroMedico:
        self._validar_datos(datos)
        return self.repository.guardar(datos)
    
    def obtener_por_id(self, registro_id: UUID) -> RegistroMedico:
        registro = self.repository.obtener_por_id(registro_id)
        if not registro:
            raise NotFoundException("registro médico", registro_id)
        return registro

    def listar_registros(self) -> List[RegistroMedico]:
        return self.repository.obtener_todos()
    
    def actualizar_registro(self, registro_id: UUID, datos: CrearRegistroMedico) -> RegistroMedico:
        self._validar_datos(datos)
        registro_actualizado = self.repository.actualizar(registro_id, datos)
        if not registro_actualizado:
            raise NotFoundException("registro médico", registro_id)
        return registro_actualizado

    def eliminar_registro(self, registro_id: UUID) -> None:
        eliminado = self.repository.eliminar(registro_id)
        if not eliminado:
            raise NotFoundException("registro médico", registro_id)