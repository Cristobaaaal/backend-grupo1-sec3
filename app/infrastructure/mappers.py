from uuid import UUID

from app.domain.models import (
    CentroPokemon,
    Entrenador,
    EstadoAtencion,
    PasswordResetToken,
    Pokemon,
    RefreshToken,
    RegistroMedico,
    RolUsuario,
    TipoPokemon,
    Usuario,
)
from app.infrastructure.models import (
    CentroPokemonORM,
    EntrenadorORM,
    PasswordResetTokenORM,
    PokemonORM,
    RefreshTokenORM,
    RegistroMedicoORM,
    UsuarioORM,
)


def entrenador_a_domain(
    modelo: EntrenadorORM,
) -> Entrenador:  # Recibe y devuelve "Entrenador"
    return Entrenador(
        id=UUID(modelo.id),
        nombre=modelo.nombre,
        nivel_experiencia=modelo.nivel_experiencia,
        region_origen=modelo.region_origen,
        medallas_obtenidas=modelo.medallas_obtenidas,
    )


def pokemon_a_domain(modelo: PokemonORM) -> Pokemon:
    return Pokemon(
        id=UUID(modelo.id),
        nombre=modelo.nombre,
        tipo_principal=TipoPokemon(modelo.tipo_principal),
        nivel=modelo.nivel,
        puntos_vida=modelo.puntos_vida,
        entrenador_id=(
            UUID(modelo.entrenador_id)
            if modelo.entrenador_id
            is not None  # Si tiene entrenador convierte su id a UUID
            else None
        ),
    )


def centro_a_domain(modelo: CentroPokemonORM) -> CentroPokemon:
    return CentroPokemon(
        id=UUID(modelo.id),
        nombre=modelo.nombre,
        ciudad=modelo.ciudad,
        capacidad_maxima=modelo.capacidad_maxima,
        en_servicio=modelo.en_servicio,
    )


def registro_a_domain(modelo: RegistroMedicoORM) -> RegistroMedico:
    return RegistroMedico(
        id=UUID(modelo.id),
        pokemon_id=UUID(modelo.pokemon_id),
        centro_id=UUID(modelo.centro_id),
        diagnostico=modelo.diagnostico,
        fecha_ingreso=modelo.fecha_ingreso,
        estado=EstadoAtencion(modelo.estado),
        costo=modelo.costo,
    )


def usuario_a_domain(modelo: UsuarioORM) -> Usuario:
    return Usuario(
        id=UUID(modelo.id),
        email=modelo.email,
        password_hash=modelo.password_hash,
        nombre_completo=modelo.nombre_completo,
        rol=RolUsuario(modelo.rol),
        activo=modelo.activo,
        intentos_fallidos=modelo.intentos_fallidos,
        bloqueado_hasta=modelo.bloqueado_hasta,
        token_version=modelo.token_version,
    )


def refresh_token_a_domain(modelo: RefreshTokenORM) -> RefreshToken:
    return RefreshToken(
        id=UUID(modelo.id),
        token_hash=modelo.token_hash,
        usuario_id=UUID(modelo.usuario_id),
        expira_en=modelo.expira_en,
        revocado=modelo.revocado,
        familia_id=modelo.familia_id,
        creado_en=modelo.creado_en,
    )


def password_reset_token_a_domain(modelo: PasswordResetTokenORM) -> PasswordResetToken:
    return PasswordResetToken(
        id=UUID(modelo.id),
        token_hash=modelo.token_hash,
        usuario_id=UUID(modelo.usuario_id),
        expira_en=modelo.expira_en,
        usado=modelo.usado,
        creado_en=modelo.creado_en,
    )
