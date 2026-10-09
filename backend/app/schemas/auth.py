# Schemas de autenticación - Pydantic
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="Mínimo 8 caracteres")
    full_name: str = Field(min_length=2, description="Nombre completo")

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = {"from_attributes": True}


class TokenRefresh(BaseModel):
    refresh_token: str

    model_config = {"from_attributes": True}


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    created_at: datetime
    email_verified: bool = False

    model_config = {"from_attributes": True}


# === Nuevos esquemas para mejoras Fase 2 ===

class VerifyEmailRequest(BaseModel):
    token: str

    model_config = {"from_attributes": True}


class ResendVerificationRequest(BaseModel):
    email: EmailStr

    model_config = {"from_attributes": True}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    model_config = {"from_attributes": True}


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, description="Mínimo 8 caracteres")
    confirm_password: str

    model_config = {"from_attributes": True}


class AuthMessageResponse(BaseModel):
    message: str

    model_config = {"from_attributes": True}