# Database - Configuración de la base de datos async
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from fastapi import Depends
from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Export for FastAPI dependencies
async_session_maker = async_session


async def get_async_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)