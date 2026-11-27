from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models import PasswordResetToken, RefreshToken
from app.infrastructure.mappers import (
    password_reset_token_a_domain,
    refresh_token_a_domain,
)
from app.infrastructure.models import PasswordResetTokenORM, RefreshTokenORM


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

    def obtener_refresh_token_por_hash(self, token_hash: str) -> RefreshToken | None:
        modelo = (
            self.db.query(RefreshTokenORM)
            .filter(RefreshTokenORM.token_hash == token_hash)
            .first()
        )
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

    def guardar_password_reset_token(
        self, token: PasswordResetToken
    ) -> PasswordResetToken:
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

    def obtener_password_reset_token_por_hash(
        self, token_hash: str
    ) -> PasswordResetToken | None:
        modelo = (
            self.db.query(PasswordResetTokenORM)
            .filter(PasswordResetTokenORM.token_hash == token_hash)
            .first()
        )
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

    # Las operaciones siguientes confirman cada flujo completo, no pasos aislados.
    def _bloquear_usuario(self, usuario_id):
        from sqlalchemy import update

        from app.infrastructure.models import UsuarioORM

        self.db.execute(
            update(UsuarioORM)
            .where(UsuarioORM.id == str(usuario_id))
            .values(token_version=UsuarioORM.token_version)
        )
        self.db.expire_all()
        return self.db.get(UsuarioORM, str(usuario_id))

    def guardar_sesion(self, token: RefreshToken, version: int) -> bool:
        from app.infrastructure.models import AuthSessionORM

        usuario = self._bloquear_usuario(token.usuario_id)
        if usuario is None or not usuario.activo or usuario.token_version != version:
            self.db.rollback()
            return False
        try:
            self.db.add(
                AuthSessionORM(
                    id=token.familia_id,
                    usuario_id=str(token.usuario_id),
                    expira_en=token.expira_en,
                    revocada=False,
                )
            )
            self.db.flush()
            self.db.add(
                RefreshTokenORM(
                    id=str(token.id),
                    token_hash=token.token_hash,
                    usuario_id=str(token.usuario_id),
                    familia_id=token.familia_id,
                    expira_en=token.expira_en,
                    revocado=False,
                    creado_en=token.creado_en,
                )
            )
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

    def sesion_vigente(self, familia_id: str, usuario_id, ahora: datetime) -> bool:
        from app.infrastructure.models import AuthSessionORM

        return (
            self.db.query(AuthSessionORM.id)
            .filter(
                AuthSessionORM.id == familia_id,
                AuthSessionORM.usuario_id == str(usuario_id),
                AuthSessionORM.revocada.is_(False),
                AuthSessionORM.expira_en > ahora,
            )
            .first()
            is not None
        )

    def _revocar_familia(self, familia_id: str):
        from app.infrastructure.models import AuthSessionORM

        self.db.query(AuthSessionORM).filter(AuthSessionORM.id == familia_id).update(
            {AuthSessionORM.revocada: True}, synchronize_session=False
        )
        self.db.query(RefreshTokenORM).filter(
            RefreshTokenORM.familia_id == familia_id
        ).update({RefreshTokenORM.revocado: True}, synchronize_session=False)

    def rotar(
        self, anterior_hash: str, nuevo_hash: str, nuevo_id: str, ahora: datetime
    ):
        from app.infrastructure.mappers import usuario_a_domain
        from app.infrastructure.models import AuthSessionORM

        anterior = (
            self.db.query(RefreshTokenORM).filter_by(token_hash=anterior_hash).first()
        )
        if anterior is None or anterior.familia_id is None:
            self.db.rollback()
            return None
        usuario_id = anterior.usuario_id
        self.db.rollback()
        try:
            usuario = self._bloquear_usuario(usuario_id)
            anterior = (
                self.db.query(RefreshTokenORM)
                .filter_by(token_hash=anterior_hash)
                .first()
            )
            familia = self.db.get(AuthSessionORM, anterior.familia_id)
            if anterior.revocado:
                # Incluye todos los descendientes y los access tokens de la sesión.
                self._revocar_familia(anterior.familia_id)
                self.db.commit()
                return None
            if (
                usuario is None
                or not usuario.activo
                or familia is None
                or familia.revocada
                or familia.expira_en <= ahora
                or anterior.expira_en <= ahora
            ):
                self.db.rollback()
                return None
            anterior.revocado = True
            self.db.add(
                RefreshTokenORM(
                    id=nuevo_id,
                    token_hash=nuevo_hash,
                    usuario_id=usuario_id,
                    familia_id=familia.id,
                    expira_en=anterior.expira_en,
                    revocado=False,
                    creado_en=ahora,
                )
            )
            resultado = (usuario_a_domain(usuario), familia.id)
            self.db.commit()
            return resultado
        except Exception:
            self.db.rollback()
            raise

    def cerrar_sesion(self, token_hash: str):
        anterior = (
            self.db.query(RefreshTokenORM).filter_by(token_hash=token_hash).first()
        )
        if anterior is None:
            self.db.rollback()
            return
        usuario_id = anterior.usuario_id
        self.db.rollback()
        try:
            self._bloquear_usuario(usuario_id)
            anterior = (
                self.db.query(RefreshTokenORM).filter_by(token_hash=token_hash).first()
            )
            if anterior.familia_id:
                self._revocar_familia(anterior.familia_id)
            else:
                anterior.revocado = True
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def limitar(
        self, identificador: str, maximo: int, ventana: int, ahora: datetime
    ) -> bool:
        import hashlib

        from sqlalchemy import update
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        from app.infrastructure.models import AuthRateLimitORM

        periodo = int(ahora.replace(tzinfo=UTC).timestamp()) // ventana
        clave = hashlib.sha256(f"{identificador}:{periodo}".encode()).hexdigest()
        insertar = sqlite_insert if self.db.bind.dialect.name == "sqlite" else pg_insert
        try:
            self.db.execute(
                insertar(AuthRateLimitORM)
                .values(clave=clave, intentos=0)
                .on_conflict_do_nothing(index_elements=["clave"])
            )
            resultado = self.db.execute(
                update(AuthRateLimitORM)
                .where(
                    AuthRateLimitORM.clave == clave, AuthRateLimitORM.intentos < maximo
                )
                .values(intentos=AuthRateLimitORM.intentos + 1)
            )
            permitido = resultado.rowcount == 1
            self.db.commit()
            return permitido
        except Exception:
            self.db.rollback()
            raise

    def preparar_recuperacion(self, token: PasswordResetToken, version: int) -> bool:
        try:
            usuario = self._bloquear_usuario(token.usuario_id)
            if (
                usuario is None
                or not usuario.activo
                or usuario.token_version != version
            ):
                self.db.rollback()
                return False
            self.db.query(PasswordResetTokenORM).filter_by(
                usuario_id=str(token.usuario_id), usado=False
            ).update({PasswordResetTokenORM.usado: True}, synchronize_session=False)
            self.db.add(
                PasswordResetTokenORM(
                    id=str(token.id),
                    token_hash=token.token_hash,
                    usuario_id=str(token.usuario_id),
                    expira_en=token.expira_en,
                    usado=False,
                    creado_en=token.creado_en,
                )
            )
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

    def consumir_recuperacion(
        self,
        token_hash: str,
        usuario_id,
        version: int,
        nuevo_hash: str,
        ahora: datetime,
    ) -> bool:
        from app.infrastructure.models import AuthSessionORM

        try:
            usuario = self._bloquear_usuario(usuario_id)
            token = (
                self.db.query(PasswordResetTokenORM)
                .filter_by(token_hash=token_hash, usuario_id=str(usuario_id))
                .first()
            )
            if (
                usuario is None
                or not usuario.activo
                or usuario.token_version != version
                or token is None
                or token.usado
                or token.expira_en <= ahora
            ):
                self.db.rollback()
                return False
            usuario.password_hash = nuevo_hash
            usuario.token_version += 1
            usuario.intentos_fallidos = 0
            usuario.bloqueado_hasta = None
            self.db.query(PasswordResetTokenORM).filter_by(
                usuario_id=str(usuario_id)
            ).update({PasswordResetTokenORM.usado: True}, synchronize_session=False)
            self.db.query(RefreshTokenORM).filter_by(usuario_id=str(usuario_id)).update(
                {RefreshTokenORM.revocado: True}, synchronize_session=False
            )
            self.db.query(AuthSessionORM).filter_by(usuario_id=str(usuario_id)).update(
                {AuthSessionORM.revocada: True}, synchronize_session=False
            )
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise
