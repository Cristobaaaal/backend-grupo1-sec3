import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError
from app.domain.models import RefreshToken, RolUsuario, Usuario
from app.repositories.token_repository import TokenRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.auth_schemas import (
    LoginRequest,
    RegistroRequest,
    TokenResponse,
)
from app.security.passwords import hash_password, verify_password
from app.security.tokens import crear_access_token


MAX_INTENTOS_FALLIDOS = 5
MINUTOS_BLOQUEO = 15
DIAS_REFRESH_TOKEN = 7


class AuthService:
    def __init__(
        self,
        usuario_repo: UsuarioRepository,
        token_repo: TokenRepository,
    ):
        self.usuario_repo = usuario_repo
        self.token_repo = token_repo

    def registrar(self, datos: RegistroRequest) -> Usuario:
        """Crea una cuenta con contraseña protegida y rol ENTRENADOR."""
        email = str(datos.email).strip().lower()

        if self.usuario_repo.obtener_por_email(email):
            raise ConflictError("Ya existe una cuenta con ese correo.")

        usuario = Usuario(
            id=uuid4(),
            email=email,
            password_hash=hash_password(datos.password),
            nombre_completo=datos.nombre_completo,
            rol=RolUsuario.ENTRENADOR,
            activo=True,
        )

        try:
            return self.usuario_repo.crear(usuario)
        except IntegrityError:
            self.usuario_repo.db.rollback()

            if self.usuario_repo.obtener_por_email(email):
                raise ConflictError(
                    "Ya existe una cuenta con ese correo."
                ) from None

            raise

    def _credenciales_invalidas(self) -> HTTPException:
        """Construye una respuesta general de autenticación fallida."""
        return HTTPException(
            status_code=401,
            detail="Credenciales inválidas o cuenta no disponible.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    def autenticar(self, datos: LoginRequest) -> Usuario:
        """Verifica credenciales y controla intentos fallidos."""
        usuario = self.usuario_repo.obtener_por_email(
            str(datos.email)
        )

        if usuario is None:
            hash_password(datos.password)
            raise self._credenciales_invalidas()

        ahora = datetime.now(timezone.utc)
        bloqueo = usuario.bloqueado_hasta

        if bloqueo is not None:
            if bloqueo.tzinfo is None:
                bloqueo = bloqueo.replace(tzinfo=timezone.utc)

            if bloqueo > ahora:
                raise self._credenciales_invalidas()

        if not usuario.activo:
            raise self._credenciales_invalidas()

        password_correcta = verify_password(
            datos.password,
            usuario.password_hash,
        )

        if not password_correcta:
            intentos = (
                1
                if bloqueo is not None
                else usuario.intentos_fallidos + 1
            )

            bloqueado_hasta = None

            if intentos >= MAX_INTENTOS_FALLIDOS:
                bloqueado_hasta = (
                    ahora + timedelta(minutes=MINUTOS_BLOQUEO)
                ).replace(tzinfo=None)

            self.usuario_repo.actualizar_intentos_fallidos(
                usuario.id,
                intentos,
                bloqueado_hasta,
            )

            raise self._credenciales_invalidas()

        self.usuario_repo.actualizar_intentos_fallidos(
            usuario.id,
            0,
            None,
        )

        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None

        return usuario

    def _emitir_tokens(self, usuario: Usuario) -> TokenResponse:
        """Genera el JWT de acceso y guarda el hash del refresh token."""
        access_token = crear_access_token(usuario.id)
        refresh_token = secrets.token_urlsafe(48)

        token_hash = hashlib.sha256(
            refresh_token.encode("utf-8")
        ).hexdigest()

        ahora = datetime.now(timezone.utc).replace(tzinfo=None)

        registro = RefreshToken(
            id=uuid4(),
            token_hash=token_hash,
            usuario_id=usuario.id,
            expira_en=ahora + timedelta(days=DIAS_REFRESH_TOKEN),
            revocado=False,
            creado_en=ahora,
        )

        self.token_repo.guardar_refresh_token(registro)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def login(self, datos: LoginRequest) -> TokenResponse:
        """Autentica al usuario y devuelve sus tokens."""
        usuario = self.autenticar(datos)
        return self._emitir_tokens(usuario)

    def logout(self, refresh_token: str) -> None:
        """Revoca la sesión asociada al refresh token."""
        token_hash = hashlib.sha256(
            refresh_token.encode("utf-8")
        ).hexdigest()

        registro = self.token_repo.obtener_refresh_token_por_hash(
            token_hash
        )

        if registro is None or registro.revocado:
            return

        self.token_repo.revocar_refresh_token(registro.id)