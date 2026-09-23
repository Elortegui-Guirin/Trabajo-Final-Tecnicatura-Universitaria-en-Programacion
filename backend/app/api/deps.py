# Dependencias de FastAPI para autenticación
from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import async_session_maker
from app.core.security import decode_token, SECRET_KEY, ALGORITHM
from app.models.user import User
from sqlmodel import select

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_session() -> Generator[AsyncSession, None, None]:
    async with async_session_maker() as session:
        yield session


async def get_current_user(
    scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Dependency: obtiene el usuario actual del token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload is None or payload.get("type") != "access":
            raise credentials_exception
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    statement = select(User).where(User.id == user_id)
    result = await session.exec(statement)
    user = result.first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency: asegura que el usuario esté activo."""
    return current_user


require_auth = SecurityScopes(scopes=["authenticated"])