from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.models import RolUsuario


class RegistroRequest(BaseModel): #Recibe email, nombre y contraseña para crear una cuenta
    email: EmailStr
    nombre_completo: str = Field(..., min_length=2, max_length=150)
    password: str = Field(..., min_length=12, max_length=128)


class LoginRequest(BaseModel): #Recibe las credenciales
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class UsuarioResponse(BaseModel):#Devuelve los datos públicos del usuario, sin contraseña ni hash
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    nombre_completo: str
    rol: RolUsuario
    activo: bool


class TokenResponse(BaseModel): #Devuelve los tokens de acceso y renovación
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel): #Recibe el token para renovar el acceso
    refresh_token: str = Field(..., min_length=1)


class LogoutRequest(BaseModel): #Recibe el token que se invalidará al cerrar sesión
    refresh_token: str = Field(..., min_length=1)