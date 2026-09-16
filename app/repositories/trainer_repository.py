from app.domain.models import Entrenador
from uuid import UUID
from typing import List, Optional

class EntrenadorRepository:
    def __init__(self):
        self._db: List[Entrenador] = [] #el _ es para ponerlo privado y el List[Entrenador] es basicamente definir el tipo de dato

    def save(self, entrenador: Entrenador) -> Entrenador:
        self._db.append(entrenador) #se agrega el entrenador a la lista d entrenadores
        return entrenador #te devuelve el entrenador que se guardo

    def get_all(self) -> List[Entrenador]:
        return self._db #va a buscarte todos los entrenadores que estan en la lista

    def get_by_id(self, entrenador_id: UUID) -> Optional[Entrenador]:
        for entrenador in self._db:
            if entrenador.id == entrenador_id: #recorre la lista buscando el entrenador con ese id
                return entrenador #te lo devuelve si lo encuentra
        return None #sino te lo pasa vacio

    def delete(self, entrenador_id: UUID) -> bool:
        trainer = self.get_by_id(entrenador_id) #busca el entrenador con ese id
        if not trainer: #si no lo encuentra
            return False 
        self._db.remove(trainer) #si encuentra al dt lo elimina
        return True #te devuelve true si lo pudo eliminar

    def update(self, entrenador_id: UUID, updated_entrenador: Entrenador) -> Optional[Entrenador]:
        trainer = self.get_by_id(entrenador_id) #busca el entrenador con ese id
        if not trainer:
            return None 
        trainer.nombre = updated_entrenador.nombre                                                                #actualiza la informacion
        trainer.region_origen = updated_entrenador.region_origen                                                         #||
        trainer.medallas_obtenidas = updated_entrenador.medallas_obtenidas                                               #||
        trainer.nivel_experiencia = updated_entrenador.nivel_experiencia                                                 #||
        return trainer #te devuelve todo del entrenador actualizado                                                      #||