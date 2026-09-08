# Health check router
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import text

from app.db.database import get_session

router = APIRouter(tags=["health"])

@router.get("/health", summary="Health check")
async def health_check(session: AsyncSession = Depends(get_session)):
    # Verificar conexión a BD
    try:
        await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"
    
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "service": "geoforraje-api",
        "version": "1.0.0"
    }

@router.get("/ready", summary="Readiness probe")
async def readiness_check(session: AsyncSession = Depends(get_session)):
    """Para Kubernetes readiness probe - verifica BD y migraciones"""
    try:
        await session.execute(text("SELECT 1"))
        # Verificar que tablas existen
        await session.execute(text("SELECT 1 FROM users LIMIT 1"))
        await session.execute(text("SELECT 1 FROM lots LIMIT 1"))
        await session.execute(text("SELECT 1 FROM analyses LIMIT 1"))
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not ready", "error": str(e)}