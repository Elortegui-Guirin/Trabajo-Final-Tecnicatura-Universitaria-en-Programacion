# Database - Configuración de la base de datos async
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

# IMPORTANTE: usar el AsyncSession de SQLModel (tiene .exec()); el de SQLAlchemy no.
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    # Tests: sin pool, para no compartir conexiones de asyncpg entre event loops
    **({"poolclass": NullPool} if settings.DB_NULLPOOL else {}),
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Export for FastAPI dependencies
async_session_maker = async_session


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


def make_worker_session_maker():
    """
    Engine + sessionmaker para workers de Celery.
    Cada task corre su propio event loop (asyncio.run), así que no se pueden
    reutilizar conexiones del pool global: se usa NullPool y se descarta el engine al final.
    """
    worker_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    maker = async_sessionmaker(worker_engine, class_=AsyncSession, expire_on_commit=False)
    return worker_engine, maker


async def init_db():
    """Crea la extensión PostGIS y las tablas que falten (modo desarrollo)."""
    # Importar modelos para que queden registrados en SQLModel.metadata
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.run_sync(SQLModel.metadata.create_all)
