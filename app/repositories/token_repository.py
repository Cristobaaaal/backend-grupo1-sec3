from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.domain.models import RefreshToken, PasswordResetToken
from app.infrastructure.models import RefreshTokenORM, PasswordResetTokenORM
from app.infrastructure.mappers import refresh_token_a_domain, password_reset_token_a_domain

class TokenRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Refresh Tokens ---

    def guardar_refresh_token(self, token: RefreshToken) -> RefreshToken:
        modelo = RefreshTokenORM(
            id=str(token.id),
            token_hash=token.token_hash,
            usuario_id=str(token.usuario_id),
            expira_en=token.expira_en,
            revocado=token.revocado,
            creado_en=token.creado_en or datetime.utcnow(),
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return refresh_token_a_domain(modelo)

    def obtener_refresh_token_por_hash(self, token_hash: str) -> Optional[RefreshToken]:
        modelo = self.db.query(RefreshTokenORM).filter(
            RefreshTokenORM.token_hash == token_hash
        ).first()
        return refresh_token_a_domain(modelo) if modelo else None

    def revocar_refresh_token(self, token_id: UUID) -> None:
        self.db.query(RefreshTokenORM).filter(
            RefreshTokenORM.id == str(token_id)
        ).update({RefreshTokenORM.revocado: True})
        self.db.commit()

    def revocar_todos_los_refresh_tokens_del_usuario(self, usuario_id: UUID) -> None:
        """Invalida todas las sesiones activas del usuario (usado en cambio de contraseña)."""
        self.db.query(RefreshTokenORM).filter(
            RefreshTokenORM.usuario_id == str(usuario_id),
            RefreshTokenORM.revocado == False,
        ).update({RefreshTokenORM.revocado: True})
        self.db.commit()

    # --- Password Reset Tokens ---

    def guardar_password_reset_token(self, token: PasswordResetToken) -> PasswordResetToken:
        modelo = PasswordResetTokenORM(
            id=str(token.id),
            token_hash=token.token_hash,
            usuario_id=str(token.usuario_id),
            expira_en=token.expira_en,
            usado=token.usado,
            creado_en=token.creado_en or datetime.utcnow(),
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return password_reset_token_a_domain(modelo)

    def obtener_password_reset_token_por_hash(self, token_hash: str) -> Optional[PasswordResetToken]:
        modelo = self.db.query(PasswordResetTokenORM).filter(
            PasswordResetTokenORM.token_hash == token_hash
        ).first()
        return password_reset_token_a_domain(modelo) if modelo else None

    def marcar_password_reset_token_usado(self, token_id: UUID) -> None:
        self.db.query(PasswordResetTokenORM).filter(
            PasswordResetTokenORM.id == str(token_id)
        ).update({PasswordResetTokenORM.usado: True})
        self.db.commit()

    def invalidar_tokens_recuperacion_pendientes(self, usuario_id: UUID) -> None:
        """Invalida cualquier otro token de recuperación pendiente del usuario."""
        self.db.query(PasswordResetTokenORM).filter(
            PasswordResetTokenORM.usuario_id == str(usuario_id),
            PasswordResetTokenORM.usado == False,
        ).update({PasswordResetTokenORM.usado: True})
        self.db.commit()
