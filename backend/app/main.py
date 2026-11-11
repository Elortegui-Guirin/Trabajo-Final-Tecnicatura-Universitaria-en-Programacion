# GeoForraje Backend - Main App
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import get_settings
from app.db.database import init_db
from app.routers import analyses, auth, health, lots

# Registrar la app de Celery (broker Redis) antes de usar .delay() en los routers
from app.workers.celery_app import celery_app  # noqa: F401

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: en desarrollo crea extensión PostGIS + tablas que falten
    if settings.AUTO_CREATE_TABLES:
        await init_db()
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title="GeoForraje API",
    version="1.0.0",
    description="API para gestión de lotes y análisis forrajero geoespacial",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# Routers
# Cada router ya define su prefijo (/auth, /lots, /analyses): no repetirlo acá,
# si no las rutas quedan /auth/auth/login, /lots/lots, etc.
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(lots.router)
app.include_router(analyses.router)


@app.get("/", include_in_schema=False)
async def root():
    return {"name": "GeoForraje API", "version": "1.0.0", "docs": "/docs"}
