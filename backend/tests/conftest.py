# Conftest para pytest-asyncio
#
# - Usa una base de datos de TEST separada (geoforraje_test), que se crea sola si no existe.
#   Se puede cambiar con la variable de entorno TEST_DATABASE_URL.
# - Crea las tablas una vez por sesión y vacía todas las tablas antes de cada test,
#   así los tests no dependen del orden ni de corridas anteriores (emails repetidos, etc.).
# - El cliente HTTP le pega directo a la app (ASGITransport), sin levantar un servidor.
# - Celery no se usa en tests: run_analysis_task.delay se reemplaza por un mock,
#   así los análisis quedan en estado "pending".
import asyncio
import os
from unittest.mock import patch

# --- Configurar entorno ANTES de importar la app (settings se lee al importar) ---
_main_url = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@postgres:5432/geoforraje"
)
_test_url = os.environ.get("TEST_DATABASE_URL") or (_main_url.rsplit("/", 1)[0] + "/geoforraje_test")
os.environ["DATABASE_URL"] = _test_url
os.environ["DB_NULLPOOL"] = "true"
os.environ["AUTO_CREATE_TABLES"] = "false"

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402
from sqlmodel.ext.asyncio.session import AsyncSession  # noqa: E402

import app.models  # noqa: E402,F401  (registra todas las tablas)
from app.db.database import async_session_maker, engine  # noqa: E402
from app.main import app  # noqa: E402

# Orden para vaciar tablas (TRUNCATE ... CASCADE igual resuelve dependencias)
_TABLES = ["analyses", "lot_versions", "lots", "audit_log", "users"]


async def _ensure_test_database() -> None:
    """Crea la base geoforraje_test si no existe (conectándose a la base 'postgres')."""
    db_name = _test_url.rsplit("/", 1)[1]
    admin_url = _test_url.rsplit("/", 1)[0] + "/postgres"
    admin_engine = create_async_engine(admin_url, poolclass=NullPool, isolation_level="AUTOCOMMIT")
    try:
        async with admin_engine.connect() as conn:
            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": db_name}
            )
            if not exists:
                await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    finally:
        await admin_engine.dispose()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_schema():
    """Crea PostGIS + tablas una vez por sesión de tests."""
    await _ensure_test_database()
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables(_create_schema):
    """Vacía todas las tablas antes de cada test."""
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {', '.join(_TABLES)} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture(autouse=True)
def _no_celery():
    """Evita encolar tareas reales en Redis durante los tests."""
    with patch("app.routers.analyses.run_analysis_task.delay") as mocked_delay:
        yield mocked_delay


@pytest.fixture(autouse=True)
def _reset_login_rate_limit():
    """El rate limit de login es en memoria: limpiarlo entre tests."""
    from app.routers import auth

    auth.login_attempts.clear()
    yield


@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
