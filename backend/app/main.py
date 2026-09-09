# GeoForraje Backend - Main App
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import get_settings
from app.db.database import init_db
from app.routers import health

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
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
app.include_router(health.router, tags=["health"])

from app.routers import auth

app.include_router(auth.router, prefix="/auth", tags=["auth"])

# TODO: FASE 3 - incluir lots router
# from app.routers import lots
# app.include_router(lots.router, prefix="/lots", tags=["lots"])

# TODO: FASE 5 - incluir analyses router
# from app.routers import analyses
# app.include_router(analyses.router, prefix="/analyses", tags=["analyses"])

@app.get("/", include_in_schema=False)
async def root():
    return {"name": "GeoForraje API", "version": "1.0.0", "docs": "/docs"}