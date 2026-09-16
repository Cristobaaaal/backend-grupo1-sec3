from typing import List
from uuid import UUID, uuid4
from app.domain.models import CentroPokemon, EstadoAtencion
from app.repositories.centro_pokemon_repository import CentroPokemonRepository
from app.schemas.schemas import CrearCentroPokemon
from app.repositories.registro_medico_repository import RegistroMedicoRepository
from app.core.exceptions import NotFoundException, BusinessRuleError

class CentroPokemonService:
    def __init__(self, centro_repo: CentroPokemonRepository, registro_repo: RegistroMedicoRepository):
        self.centro_repo = centro_repo
        self.registro_repo = registro_repo

    def crear_centro(self, datos: CrearCentroPokemon) -> CentroPokemon:
        if datos.capacidad_maxima <= 0:
            raise ValueError("La capacidad máxima del centro debe ser mayor a 0.")

        nuevo_centro = CentroPokemon(
            id=uuid4(),
            nombre=datos.nombre,
            ciudad=datos.ciudad,
            capacidad_maxima=datos.capacidad_maxima,
            en_servicio=datos.en_servicio,
        )

        return self.centro_repo.save(nuevo_centro)

    def obtener_todos(self) -> List[CentroPokemon]:
        return self.centro_repo.get_all()

    def obtener_por_id(self, centro_id: UUID) -> CentroPokemon:
        centro = self.centro_repo.get_by_id(centro_id)
        if not centro:
            raise NotFoundException("centro pokémon", centro_id)
        return centro

    def obtener_por_ciudad(self, ciudad: str) -> List[CentroPokemon]:
        return self.centro_repo.get_by_ciudad(ciudad)

    def eliminar_centro_pokemon(self, centro_id: UUID) -> None:
        self.obtener_por_id(centro_id)
        tiene_pacientes_activos = any(
            r.centro_id == centro_id and r.estado == EstadoAtencion.EN_TRATAMIENTO
            for r in self.registro_repo.obtener_todos()
        )
        if tiene_pacientes_activos:
            raise BusinessRuleError(
                f"No se puede eliminar el centro {centro_id}: tiene pokemones en tratamiento.")
        self.centro_repo.delete(centro_id)
    
    def actualizar_centro_pokemon(self, centro_id: UUID, datos: CrearCentroPokemon) -> CentroPokemon:
        actualizado = self.centro_repo.actualizar(centro_id, datos)
        if not actualizado:
            raise NotFoundException("centro pokémon", centro_id)
        return actualizado