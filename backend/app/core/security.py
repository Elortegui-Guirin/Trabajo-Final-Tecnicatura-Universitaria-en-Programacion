# Security - JWT y hash de contraseñas
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
from uuid import UUID
import secrets

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Valores tomados de la configuración (.env / variables de entorno)
_settings = get_settings()
SECRET_KEY = _settings.JWT_SECRET
ALGORITHM = _settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = _settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = _settings.REFRESH_TOKEN_EXPIRE_DAYS
VERIFICATION_TOKEN_EXPIRE_HOURS = 24
RESET_TOKEN_EXPIRE_HOURS = 1


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _prepare_claims(data: dict) -> dict:
    """Copia los claims y convierte "sub" a str (los UUID no son serializables a JSON)."""
    to_encode = data.copy()
    if "sub" in to_encode and to_encode["sub"] is not None:
        to_encode["sub"] = str(to_encode["sub"])
    return to_encode


def parse_user_id(sub) -> Optional[UUID]:
    """Convierte el claim "sub" del token en UUID (None si es inválido)."""
    try:
        return UUID(str(sub))
    except (TypeError, ValueError):
        return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = _prepare_claims(data)
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, jti: Optional[str] = None) -> str:
    """
    Refresh token con identificador único (jti). El jti vigente se guarda en
    User.refresh_token_jti: al rotar se reemplaza, así el token anterior deja de servir.
    """
    to_encode = _prepare_claims(data)
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh", "jti": jti or secrets.token_hex(16)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_verification_token(data: dict) -> str:
    """Crea token para verificación de email (expira en 24h)."""
    to_encode = _prepare_claims(data)
    expire = datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire, "type": "verification"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_reset_token(data: dict) -> str:
    """Crea token para reset de contraseña (expira en 1h)."""
    to_encode = _prepare_claims(data)
    expire = datetime.now(timezone.utc) + timedelta(hours=RESET_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire, "type": "reset"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return {}


def generate_secure_token() -> str:
    """Genera token seguro para verificación/reset (no JWT, solo random)."""
    return secrets.token_urlsafe(32)


def get_password_hash() -> str:
    """Retorna la configuración actual de Context para compatibilidad."""
    return pwd_context