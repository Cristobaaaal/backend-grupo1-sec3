from app.domain.models import Pokemon, TipoPokemon
from app.repositories.pokemon_repository import PokemonRepository
from app.repositories.trainer_repository import EntrenadorRepository
from app.schemas.schemas import CrearPokemon, PaginatedResponse
from app.core.exceptions import NotFoundException, BusinessRuleError
from typing import List, Optional
from uuid import UUID, uuid4

class PokemonService:
    def __init__(self, repository: PokemonRepository, trainer_repository: EntrenadorRepository):
        self.repository = repository
        self.trainer_repository = trainer_repository

    def _validar_entrenador_existe(self, entrenador_id: Optional[UUID]) -> None:
        if entrenador_id is not None and not self.trainer_repository.get_by_id(entrenador_id):
            raise NotFoundException("entrenador", entrenador_id)

    def crear_pokemon(self, datos: CrearPokemon) -> Pokemon: # es el tipo de dato q se espera
        self._validar_entrenador_existe(datos.entrenador_id)
        pokemon = Pokemon(
            id=uuid4(),
            nombre=datos.nombre,
            tipo_principal=datos.tipo_principal,
            nivel=datos.nivel,
            puntos_vida=datos.puntos_vida,
            entrenador_id=datos.entrenador_id
        )
        return self.repository.save(pokemon)
    
    def obtener_todos(self) -> List[Pokemon]:
        return self.repository.get_all() #llama a todos los pokemones

    ATRIBUTOS_ORDENABLES = {"nombre", "nivel", "puntos_vida"}

    def listar_paginado(
            self,
            tipo: Optional[TipoPokemon] = None,
            ordenar_por: str = "nombre",
            direccion: str = "asc",
            pagina: int = 1,
            limite: int = 20,
    )  -> PaginatedResponse:
        if ordenar_por not in self.ATRIBUTOS_ORDENABLES:
            raise BusinessRuleError(
                f"ordenar_por debe ser uno de: {', '.join(sorted(self.ATRIBUTOS_ORDENABLES))}"
            )
        if direccion not in ("asc", "desc"):
            raise BusinessRuleError("direccion debe ser 'asc' o 'desc'.")
        if pagina < 1:
            raise BusinessRuleError("pagina debe ser mayor o igual a 1.")
        if not (1 <= limite <= 100):
            raise BusinessRuleError("limite debe estar entre 1 y 100.")

        # 1) Filtrar
        pokemones = self.repository.get_all()
        if tipo is not None:
            pokemones = [p for p in pokemones if p.tipo_principal == tipo]

        # 2) Ordenar
        pokemones = sorted(
            pokemones,
            key=lambda p: getattr(p, ordenar_por),
            reverse=(direccion == "desc"),
        )

        # 3) Paginación
        total = len(pokemones)
        total_paginas = (total + limite - 1) // limite if total > 0 else 0
        inicio = (pagina - 1) * limite
        items = pokemones[inicio: inicio + limite]

        return PaginatedResponse(
            items=items,
            total=total,
            pagina=pagina,
            limite=limite,
            total_paginas=total_paginas,
        )

    def obtener_por_id(self, pokemon_id: UUID) -> Pokemon:
        pokemon = self.repository.get_by_id(pokemon_id) #lo busca por id
        if not pokemon:
            raise NotFoundException("pokemon", pokemon_id) #si no esta le manda un error
        return pokemon

    def obtener_por_tipo(self, tipo: TipoPokemon) -> List[Pokemon]:
        return self.repository.get_by_tipo(tipo)

    def obtener_por_entrenador(self, entrenador_id: UUID) -> List[Pokemon]:
        return self.repository.get_by_entrenador_id(entrenador_id)

    def obtener_sin_entrenador(self) -> List[Pokemon]:
        return self.repository.get_sin_entrenador()

    def asignar_entrenador(self, pokemon_id: UUID, entrenador_id: UUID) -> Pokemon:
        self._validar_entrenador_existe(entrenador_id)
        pokemon = self.obtener_por_id(pokemon_id)
        if pokemon.entrenador_id is not None:
            # Regla de negocio: no se puede "asignar" un pokemon que ya tiene entrenador
            raise BusinessRuleError(
                f"El pokemon {pokemon_id} ya tiene un entrenador asignado. Usa transferir en vez de asignar."
            )
        pokemon.entrenador_id = entrenador_id
        return pokemon

    def transferir_entrenador(self, pokemon_id: UUID, nuevo_entrenador_id: UUID) -> Pokemon:
        self._validar_entrenador_existe(nuevo_entrenador_id)
        pokemon = self.obtener_por_id(pokemon_id)
        if pokemon.entrenador_id == nuevo_entrenador_id:
            # Regla de negocio: no tiene sentido transferir un pokemon al mismo entrenador que ya tiene
            raise BusinessRuleError(
                f"El pokemon {pokemon_id} ya pertenece al entrenador {nuevo_entrenador_id}."
            )
        pokemon.entrenador_id = nuevo_entrenador_id
        return pokemon

    def liberar_pokemon(self, pokemon_id: UUID) -> Pokemon:
        pokemon = self.obtener_por_id(pokemon_id)
        pokemon.entrenador_id = None
        return pokemon

    def actualizar_stats(self, pokemon_id: UUID, nivel: int, puntos_vida: int) -> Pokemon:
        pokemon = self.obtener_por_id(pokemon_id)
        pokemon.nivel = nivel
        pokemon.puntos_vida = puntos_vida
        return pokemon

    def eliminar_pokemon(self, pokemon_id: UUID) -> None:
        eliminado = self.repository.delete(pokemon_id)
        if not eliminado:
            raise NotFoundException("pokemon", pokemon_id)

    def actualizar_pokemon(self, pokemon_id: UUID, datos: CrearPokemon) -> Pokemon:
        self._validar_entrenador_existe(datos.entrenador_id)
        pokemon_actualizado = self.repository.update(pokemon_id, datos)
        if not pokemon_actualizado:
            raise NotFoundException("pokemon", pokemon_id)
        return pokemon_actualizado