from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models import Usuario
from app.infrastructure.mappers import usuario_a_domain
from app.infrastructure.models import UsuarioORM


class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def obtener_por_id(self, usuario_id: UUID) -> Usuario | None:
        modelo = (
            self.db.query(UsuarioORM).filter(UsuarioORM.id == str(usuario_id)).first()
        )
        return usuario_a_domain(modelo) if modelo else None

    def obtener_por_email(self, email: str) -> Usuario | None:
        modelo = (
            self.db.query(UsuarioORM)
            .filter(UsuarioORM.email == email.strip().lower())
            .first()
        )
        return usuario_a_domain(modelo) if modelo else None

    def crear(self, usuario: Usuario) -> Usuario:
        modelo = UsuarioORM(
            id=str(usuario.id),
            email=usuario.email.strip().lower(),
            password_hash=usuario.password_hash,
            nombre_completo=usuario.nombre_completo,
            rol=usuario.rol.value
            if hasattr(usuario.rol, "value")
            else str(usuario.rol),
            activo=usuario.activo,
            intentos_fallidos=usuario.intentos_fallidos,
            bloqueado_hasta=usuario.bloqueado_hasta,
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return usuario_a_domain(modelo)

    def actualizar_intentos_fallidos(
        self, usuario_id: UUID, intentos: int, bloqueado_hasta: datetime | None = None
    ) -> None:
        self.db.query(UsuarioORM).filter(UsuarioORM.id == str(usuario_id)).update(
            {
                UsuarioORM.intentos_fallidos: intentos,
                UsuarioORM.bloqueado_hasta: bloqueado_hasta,
            }
        )
        self.db.commit()

    def restablecer_password(self, usuario_id: UUID, nuevo_password_hash: str) -> None:
        self.db.query(UsuarioORM).filter(UsuarioORM.id == str(usuario_id)).update(
            {
                UsuarioORM.password_hash: nuevo_password_hash,
                UsuarioORM.intentos_fallidos: 0,
                UsuarioORM.bloqueado_hasta: None,
            }
        )
        self.db.commit()
