from uuid import UUID, uuid4
from typing import List, Optional
from app.domain.models import RegistroMedico
from app.schemas.schemas import CrearRegistroMedico

class RegistroMedicoRepository:
    def __init__(self):
        self._registros: dict[UUID, RegistroMedico] = {}

    def guardar(self, datos: CrearRegistroMedico) -> RegistroMedico:
        nuevo_id = uuid4()
        registro = RegistroMedico(
            id=nuevo_id,
            pokemon_id=datos.pokemon_id,
            centro_id=datos.centro_id,
            diagnostico=datos.diagnostico,
            fecha_ingreso=datos.fecha_ingreso,
            estado=datos.estado,
            costo=datos.costo
        )
        self._registros[nuevo_id] = registro
        return registro

    def obtener_por_id(self, registro_id: UUID) -> Optional[RegistroMedico]:
        return self._registros.get(registro_id)

    def obtener_todos(self) -> List[RegistroMedico]:
        return list(self._registros.values())
    
    def actualizar(self, registro_id: UUID, datos: CrearRegistroMedico) -> Optional[RegistroMedico]:
        if registro_id not in self._registros:
            return None
        # Mantiene el mismo ID pero actualiza los campos
        registro_actualizado = RegistroMedico(
            id=registro_id,
            pokemon_id=datos.pokemon_id,
            centro_id=datos.centro_id,
            diagnostico=datos.diagnostico,
            fecha_ingreso=datos.fecha_ingreso,
            estado=datos.estado,
            costo=datos.costo
        )
        self._registros[registro_id] = registro_actualizado
        return registro_actualizado

    def eliminar(self, registro_id: UUID) -> bool:
        if registro_id in self._registros:
            del self._registros[registro_id]
            return True
        return False