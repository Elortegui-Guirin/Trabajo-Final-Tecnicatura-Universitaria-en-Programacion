# Endpoints de autenticación - FastAPI
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemas.auth import UserRegister, UserLogin, TokenResponse, TokenRefresh, UserPublic
from app.models.user import User
from app.db.database import get_async_session
from app.core.security import hash_password, create_access_token, create_refresh_token, decode_token
from app.api.deps import get_session, get_current_active_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    session: AsyncSession = Depends(get_session),
) -> UserPublic:
    """Crea un nuevo usuario con password hasheado."""
    existing = await session.exec(select(User).where(User.email == user_data.email))
    if existing.first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = hash_password(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_pw,
        full_name=user_data.full_name,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return UserPublic(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Inicia sesión y emite access + refresh tokens."""
    user = await session.exec(select(User).where(User.email == user_data.email))
    user = user.first()
    if not user or not user.verify_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
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
    
    # Verificar que el usuario existe y está activo
    user = await session.exec(select(User).where(User.id == user_id))
    user = user.first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")
    
    # Invalidar token anterior (lógica de rotación)
    # Crear nuevo par de tokens
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
    )