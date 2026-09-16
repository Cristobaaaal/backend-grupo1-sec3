from app.domain.models import Entrenador
from app.repositories.trainer_repository import EntrenadorRepository
from app.schemas.schemas import CrearEntrenador
from app.core.exceptions import NotFoundException
from typing import List
from uuid import UUID, uuid4

class EntrenadorService:
    def __init__(self, repository: EntrenadorRepository):
        self.repository = repository
 
    def crear_entrenador(self, datos: CrearEntrenador) -> Entrenador: # es el tipo de dato q se espera
        entrenador = Entrenador(
            id=uuid4(),
            nombre=datos.nombre,
            nivel_experiencia=datos.nivel_experiencia,
            medallas_obtenidas = datos.medallas_obtenidas,
            region_origen = datos.region_origen
        )
        return self.repository.save(entrenador)
    
    def obtener_todos(self) -> List[Entrenador]:
        return self.repository.get_all() #llama a todos los entrenadores

    def obtener_por_id(self, entrenador_id: UUID) -> Entrenador:
        entrenador = self.repository.get_by_id(entrenador_id) #lo busca por id
        if not entrenador:
            raise NotFoundException("entrenador", entrenador_id)
        return entrenador

    def actualizar_entrenador(self, entrenador_id: UUID, datos: CrearEntrenador) -> Entrenador:
        entrenador_existente = self.repository.get_by_id(entrenador_id) #se crea una variable para buscarlo
        if not entrenador_existente: #se busca
            raise NotFoundException("entrenador", entrenador_id)
        entrenador_listo = Entrenador( #si es q esta, se crea un nuevo entrenador con los datos actualizados
            id=entrenador_id,
            nombre=datos.nombre,
            nivel_experiencia=datos.nivel_experiencia,
            medallas_obtenidas=datos.medallas_obtenidas,
            region_origen=datos.region_origen)
        return self.repository.update(entrenador_id, entrenador_listo)

    def eliminar_entrenador(self, entrenador_id: UUID) -> None:
        entrenador_existente = self.repository.get_by_id(entrenador_id) # se crea una variable para buscarloo
        if not entrenador_existente:
            raise NotFoundException("entrenador", entrenador_id)
        self.repository.delete(entrenador_id) #si lo pilla lo elimina de la memoria por su id