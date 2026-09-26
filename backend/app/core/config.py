# Config - Configuración de la aplicación
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/geoforraje"

    # JWT
    JWT_SECRET: str = "tu-clave-secreta-min-32-chars-cambiar-en-produccion"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # Raster
    RASTER_DATA_PATH: str = "/data/rasters"

    # Redis (Celery)
    REDIS_URL: str = "redis://redis:6379/0"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Monitoring
    SENTRY_DSN: str = ""


settings = Settings()


def get_settings() -> Settings:
    return settings