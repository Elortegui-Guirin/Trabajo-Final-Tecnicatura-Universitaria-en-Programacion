# Endpoints de autenticación - FastAPI
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.schemas.auth import (
    UserRegister, UserLogin, TokenResponse, TokenRefresh, UserPublic,
    VerifyEmailRequest, ResendVerificationRequest,
    ForgotPasswordRequest, ResetPasswordRequest, AuthMessageResponse
)
from app.models.user import User
from app.db.database import get_async_session
from app.core.security import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_token, create_verification_token, create_reset_token,
    generate_secure_token
)
from app.api.deps import get_session, get_current_active_user
from app.core.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

# Rate limiting simple en memoria (para producción usar Redis)
login_attempts = {}


def check_rate_limit(ip: str, max_attempts: int = 10, window_minutes: int = 15) -> bool:
    """Rate limiting simple por IP."""
    now = datetime.now()
    if ip not in login_attempts:
        login_attempts[ip] = []
    
    # Limpiar intentos antiguos
    cutoff = datetime.now() - timedelta(minutes=window_minutes)
    login_attempts[ip] = [attempt for attempt in login_attempts[ip] if attempt > cutoff]
    
    if len(login_attempts[ip]) >= max_attempts:
        return False
    
    login_attempts[ip].append(datetime.now())
    return True


def record_login_attempt(ip: str) -> None:
    """Registra intento de login para rate limiting."""
    if ip not in login_attempts:
        login_attempts[ip] = []
    login_attempts[ip].append(datetime.now())


async def send_verification_email(email: str, token: str) -> None:
    """
    Envía email de verificación.
    En producción: integrar con SendGrid, Mailgun, SES, etc.
    Por ahora: log para desarrollo.
    """
    verification_url = f"{settings.CORS_ORIGINS[0]}/verify-email?token={token}"
    print(f"=== EMAIL VERIFICACIÓN ===")
    print(f"Para: {email}")
    print(f"URL: {verification_url}")
    print(f"Token: {token}")
    print(f"==========================")
    # TODO: Integrar con servicio de email real


async def send_reset_email(email: str, token: str) -> None:
    """
    Envía email para reset de contraseña.
    En producción: integrar con servicio de email real.
    """
    reset_url = f"{settings.CORS_ORIGINS[0]}/reset-password?token={token}"
    print(f"=== EMAIL RESET PASSWORD ===")
    print(f"Para: {email}")
    print(f"URL: {reset_url}")
    print(f"Token: {token}")
    print(f"============================")
    # TODO: Integrar con servicio de email real


async def send_password_changed_email(email: str) -> None:
    """Notifica cambio de contraseña por seguridad."""
    print(f"=== ALERTA CAMBIO PASSWORD ===")
    print(f"Usuario: {email} cambió su contraseña")
    print(f"Fecha: {datetime.now()}")
    print(f"==============================")


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    session: AsyncSession = Depends(get_session),
) -> UserPublic:
    """Crea un nuevo usuario con password hasheado y envía email de verificación."""
    # Verificar si email ya existe (incluyendo soft-deleted)
    existing = await session.exec(select(User).where(User.email == user_data.email))
    if existing.first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = hash_password(user_data.password)
    verification_token = generate_secure_token()
    verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    
    user = User(
        email=user_data.email,
        hashed_password=hashed_pw,
        full_name=user_data.full_name,
        verification_token=verification_token,
        verification_token_expires=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    # Enviar email de verificación (async, no bloquear respuesta)
    await send_verification_email(user.email, verification_token)
    
    return UserPublic(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at,
        email_verified=user.email_verified,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    user_data: UserLogin,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Inicia sesión y emite access + refresh tokens con control de intentos."""
    client_ip = request.client.host if request.client else "unknown"
    
    # Rate limiting por IP
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos. Intente de nuevo en 15 minutos."
        )
    
    record_login_attempt(client_ip)
    
    user = await session.exec(select(User).where(User.email == user_data.email))
    user = user.first()
    
    # Verificar cuenta bloqueada
    if user and user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Cuenta bloqueada temporalmente. Intente de nuevo después de {user.locked_until.strftime('%H:%M') if user.locked_until else 'unos minutos'}."
        )
    
    if not user or not user.verify_password(user_data.password):
        # Registrar intento fallido en BD si usuario existe
        if user:
            user.record_failed_login()
            await session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar usuario activo y no soft-deleted
    if not user.is_active or user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo o eliminado"
        )
    
    # Verificar email verificado (opcional: permitir login pero avisar)
    # if not user.email_verified:
    #     raise HTTPException(status_code=403, detail="Email no verificado")
    
    # Login exitoso: resetear contadores
    user.reset_failed_logins()
    user.last_login = datetime.now(timezone.utc)
    await session.commit()
    
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    token_data: TokenRefresh,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Rota refresh token: invalida el anterior y emite nuevo par."""
    payload = decode_token(token_data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # Verificar que el usuario existe, está activo y no soft-deleted
    user = await session.exec(select(User).where(User.id == user_id))
    user = user.first()
    if user is None or not user.is_active or user.deleted_at:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")
    
    # Invalidar token anterior (lógica de rotación)
    access_token = create_access_token(data={"sub": user.id})
    new_refresh_token = create_refresh_token(data={"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.get("/me", response_model=UserPublic)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserPublic:
    """Obtiene datos del usuario actual."""
    return UserPublic(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        created_at=current_user.created_at,
        email_verified=current_user.email_verified,
    )


# === NUEVOS ENDPOINTS PARA MEJORAS FASE 2 ===

@router.post("/verify-email", response_model=AuthMessageResponse)
async def verify_email(
    verify_data: VerifyEmailRequest,
    session: AsyncSession = Depends(get_session),
) -> AuthMessageResponse:
    """Verifica email del usuario con token."""
    payload = decode_token(verify_data.token)
    if payload is None or payload.get("type") != "verification":
        # Intentar con token seguro (no JWT)
        user = await session.exec(
            select(User).where(User.verification_token == verify_data.token)
        )
        user = user.first()
        
        if not user or user.verification_token != verify_data.token:
            raise HTTPException(status_code=400, detail="Token de verificación inválido")
        
        if user.verification_token_expires and datetime.now(timezone.utc) > user.verification_token_expires:
            raise HTTPException(status_code=400, detail="Token de verificación expirado")
        
        user.email_verified = True
        user.verification_token = None
        user.verification_token_expires = None
        await session.commit()
        return AuthMessageResponse(message="Email verificado correctamente")
    
    # Token JWT válido
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Token inválido")
    
    user = await session.exec(select(User).where(User.id == user_id))
    user = user.first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")
    
    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    await session.commit()
    
    return AuthMessageResponse(message="Email verificado correctamente")


@router.post("/resend-verification", response_model=AuthMessageResponse)
async def resend_verification(
    request: ResendVerificationRequest,
    session: AsyncSession = Depends(get_session),
) -> AuthMessageResponse:
    """Reenvía email de verificación."""
    user = await session.exec(select(User).where(User.email == request.email))
    user = user.first()
    
    if not user:
        # No revelar si email existe por seguridad
        return AuthMessageResponse(message="Si el email existe, se enviará un nuevo enlace de verificación")
    
    if user.email_verified:
        return AuthMessageResponse(message="El email ya está verificado")
    
    if user.deleted_at:
        return AuthMessageResponse(message="Si el email existe, se enviará un nuevo enlace de verificación")
    
    # Generar nuevo token
    verification_token = generate_secure_token()
    user.verification_token = verification_token
    user.verification_token_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    await session.commit()
    
    await send_verification_email(user.email, verification_token)
    
    return AuthMessageResponse(message="Si el email existe, se enviará un nuevo enlace de verificación")


@router.post("/forgot-password", response_model=AuthMessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_session),
) -> AuthMessageResponse:
    """Solicita reset de contraseña - envía email con token."""
    user = await session.exec(select(User).where(User.email == request.email))
    user = user.first()
    
    if not user or user.deleted_at:
        # No revelar si email existe por seguridad
        return AuthMessageResponse(message="Si el email existe, se enviará un enlace para restablecer la contraseña")
    
    # Generar token de reset
    reset_token = generate_secure_token()
    user.reset_token = reset_token
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    await session.commit()
    
    await send_reset_email(user.email, reset_token)
    
    return AuthMessageResponse(message="Si el email existe, se enviará un enlace para restablecer la contraseña")


@router.post("/reset-password", response_model=AuthMessageResponse)
async def reset_password(
    reset_data: ResetPasswordRequest,
    session: AsyncSession = Depends(get_session),
) -> AuthMessageResponse:
    """Restablece contraseña con token."""
    # Validar que las contraseñas coincidan
    if reset_data.new_password != reset_data.confirm_password:
        raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")
    
    user = await session.exec(select(User).where(User.reset_token == reset_data.token))
    user = user.first()
    
    if not user or user.reset_token != reset_data.token:
        raise HTTPException(status_code=400, detail="Token de restablecimiento inválido")
    
    if user.reset_token_expires and datetime.now(timezone.utc) > user.reset_token_expires:
        raise HTTPException(status_code=400, detail="Token de restablecimiento expirado")
    
    # Actualizar contraseña
    user.hashed_password = hash_password(reset_data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    user.reset_failed_logins()  # Resetear intentos fallidos
    await session.commit()
    
    # Notificar cambio por seguridad
    await send_password_changed_email(user.email)
    
    return AuthMessageResponse(message="Contraseña restablecida correctamente. Ya puede iniciar sesión.")


@router.post("/logout", response_model=AuthMessageResponse)
async def logout() -> AuthMessageResponse:
    """
    Logout del lado del servidor.
    Nota: Con JWT stateless, el logout real se hace en frontend borrando tokens.
    Este endpoint es para logging/auditoría.
    """
    return AuthMessageResponse(message="Sesión cerrada correctamente")


# Endpoint legacy mantenido por compatibilidad
@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    token_data: TokenRefresh,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Rota refresh token: invalida el anterior y emite nuevo par."""
    payload = decode_token(token_data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    user = await session.exec(select(User).where(User.id == user_id))
    user = user.first()
    if user is None or not user.is_active or user.deleted_at:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")
    
    access_token = create_access_token(data={"sub": user.id})
    new_refresh_token = create_refresh_token(data={"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.get("/me", response_model=UserPublic)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserPublic:
    """Obtiene datos del usuario actual."""
    return UserPublic(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        created_at=current_user.created_at,
        email_verified=current_user.email_verified,
    )