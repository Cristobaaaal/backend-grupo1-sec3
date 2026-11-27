import hashlib
import logging
import secrets
import smtplib
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import APIException, AuthenticationError, ConflictError
from app.domain.models import PasswordResetToken, RefreshToken, RolUsuario, Usuario
from app.repositories.token_repository import TokenRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.auth_schemas import (
    LoginRequest,
    RegistroRequest,
    TokenResponse,
)
from app.security.mail import enviar_recuperacion
from app.security.passwords import hash_password, verify_password
from app.security.tokens import (
    crear_access_token,
    crear_reset_token,
    decodificar_reset_token,
    validar_configuracion_access,
)

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
                raise ConflictError("Ya existe una cuenta con ese correo.") from None

            raise

    def _credenciales_invalidas(self) -> AuthenticationError:
        """Construye una respuesta general de autenticación fallida."""
        return AuthenticationError()

    def autenticar(self, datos: LoginRequest) -> Usuario:
        """Verifica credenciales y controla intentos fallidos."""
        usuario = self.usuario_repo.obtener_por_email(str(datos.email))

        if usuario is None:
            hash_password(datos.password)
            raise self._credenciales_invalidas()

        ahora = datetime.now(UTC)
        bloqueo = usuario.bloqueado_hasta

        if bloqueo is not None:
            if bloqueo.tzinfo is None:
                bloqueo = bloqueo.replace(tzinfo=UTC)

            if bloqueo > ahora:
                raise self._credenciales_invalidas()

        if not usuario.activo:
            raise self._credenciales_invalidas()

        password_correcta = verify_password(
            datos.password,
            usuario.password_hash,
        )

        if not password_correcta:
            intentos = 1 if bloqueo is not None else usuario.intentos_fallidos + 1

            bloqueado_hasta = None

            if intentos >= MAX_INTENTOS_FALLIDOS:
                bloqueado_hasta = (ahora + timedelta(minutes=MINUTOS_BLOQUEO)).replace(
                    tzinfo=None
                )

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
        familia_id = str(uuid4())
        access_token = crear_access_token(usuario.id, familia_id, usuario.token_version)
        refresh_token = secrets.token_urlsafe(48)

        token_hash = hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()

        ahora = datetime.now(UTC).replace(tzinfo=None)

        registro = RefreshToken(
            id=uuid4(),
            token_hash=token_hash,
            usuario_id=usuario.id,
            expira_en=ahora + timedelta(days=DIAS_REFRESH_TOKEN),
            revocado=False,
            creado_en=ahora,
            familia_id=familia_id,
        )

        if not self.token_repo.guardar_sesion(registro, usuario.token_version):
            raise AuthenticationError()

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
        token_hash = hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()

        self.token_repo.cerrar_sesion(token_hash)

    def refresh(self, refresh_token: str) -> TokenResponse:
        nuevo = secrets.token_urlsafe(48)
        # Valida la configuración antes de consumir el token actual.
        validar_configuracion_access()
        resultado = self.token_repo.rotar(
            self._hash(refresh_token),
            self._hash(nuevo),
            str(uuid4()),
            self._ahora(),
        )
        if resultado is None:
            raise AuthenticationError("Refresh token inválido, vencido o revocado.")
        usuario, familia_id = resultado
        return TokenResponse(
            access_token=crear_access_token(
                usuario.id, familia_id, usuario.token_version
            ),
            refresh_token=nuevo,
        )

    @staticmethod
    def _hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _ahora():
        return datetime.now(UTC).replace(tzinfo=None)

    def solicitar_recuperacion(self, email: str, origen: str) -> None:
        email = str(email).strip().lower()
        ahora = self._ahora()
        por_ip = self.token_repo.limitar(f"reset-ip:{origen}", 20, 900, ahora)
        por_correo = self.token_repo.limitar(f"reset-email:{email}", 3, 900, ahora)
        # Misma respuesta para cuentas inexistentes y solicitudes limitadas.
        if not por_ip or not por_correo:
            return
        usuario = self.usuario_repo.obtener_por_email(email)
        if usuario is None or not usuario.activo:
            return
        token = crear_reset_token(usuario.id, usuario.token_version)
        contenido = decodificar_reset_token(token)
        registro = PasswordResetToken(
            id=UUID(contenido["jti"]),
            usuario_id=usuario.id,
            token_hash=self._hash(token),
            creado_en=ahora,
            expira_en=datetime.fromtimestamp(contenido["exp"], UTC).replace(
                tzinfo=None
            ),
        )
        if self.token_repo.preparar_recuperacion(registro, usuario.token_version):
            try:
                enviar_recuperacion(email, token)
            except (OSError, smtplib.SMTPException):
                logging.getLogger(__name__).error(
                    "No se pudo entregar el correo de recuperación."
                )

    def restablecer(self, token: str, password: str, origen: str) -> None:
        if not self.token_repo.limitar(
            f"reset-confirm:{origen}", 20, 900, self._ahora()
        ):
            raise APIException(
                "Demasiados intentos. Intenta más tarde.", "RATE_LIMITED", 429
            )
        try:
            contenido = decodificar_reset_token(token)
        except jwt.InvalidTokenError:
            raise AuthenticationError(
                "Token de recuperación inválido o vencido."
            ) from None
        if not self.token_repo.consumir_recuperacion(
            self._hash(token),
            UUID(contenido["sub"]),
            contenido["ver"],
            hash_password(password),
            self._ahora(),
        ):
            raise AuthenticationError("Token de recuperación inválido o vencido.")
