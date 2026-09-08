from uuid import UUID
from typing import List, Optional
from app.domain.models import RegistroMedico
from app.schemas.schemas import CrearRegistroMedico
from app.repositories.registro_medico_repository import RegistroMedicoRepository

class RegistroMedicoService:
    def __init__(self, repository: RegistroMedicoRepository):
        self.repository = repository

    def crear_registro(self, datos: CrearRegistroMedico) -> RegistroMedico:
        return self.repository.guardar(datos)

    def obtener_por_id(self, registro_id: UUID) -> Optional[RegistroMedico]:
        return self.repository.obtener_por_id(registro_id)

    def listar_registros(self) -> List[RegistroMedico]:
        return self.repository.obtener_todos()