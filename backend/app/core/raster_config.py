# Configuración de catálogo raster con versionado
from typing import Dict, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class ResourceType(str, Enum):
    RESOURCE_1 = "resource_1"
    RESOURCE_2 = "resource_2"
    RESOURCE_3 = "resource_3"
    RESOURCE_4 = "resource_4"


class RasterSource(BaseModel):
    path: str
    band: int = 1
    nodata: Optional[float] = None
    description: str = ""
    crs: Optional[str] = None  # Si None, se detecta del archivo
    
    # === VERSIONADO ===
    version: str = Field(default="v1.0.0", description="Versión del raster (ej: v2024.1, v2024.2)")
    date: datetime = Field(default_factory=datetime.utcnow, description="Fecha del raster")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales")


# Catálogo de recursos forrajeros con versionado
RASTER_CATALOG: Dict[ResourceType, RasterSource] = {
    ResourceType.RESOURCE_1: RasterSource(
        path="/data/rasters/resource_1.tif",
        band=1,
        nodata=-9999,
        description="Biomasa verde (kg/ha)",
        version="v2024.1",
        date=datetime(2024, 1, 15),
        metadata={"source": "Sentinel-2", "resolution_m": 10, "band": "B08"},
    ),
    ResourceType.RESOURCE_2: RasterSource(
        path="/data/rasters/resource_2.tif",
        band=1,
        nodata=-9999,
        description="Cobertura suelo (%)",
        version="v2024.1",
        date=datetime(2024, 1, 15),
        metadata={"source": "Sentinel-2", "resolution_m": 10, "band": "B04"},
    ),
    ResourceType.RESOURCE_3: RasterSource(
        path="/data/rasters/resource_3.tif",
        band=1,
        nodata=-9999,
        description="Índice de vegetación (NDVI/EVI)",
        version="v2024.1",
        date=datetime(2024, 1, 15),
        metadata={"source": "Sentinel-2", "resolution_m": 10, "index": "NDVI"},
    ),
    ResourceType.RESOURCE_4: RasterSource(
        path="/data/rasters/resource_4.tif",
        band=1,
        nodata=-9999,
        description="Humedad suelo (%)",
        version="v2024.1",
        date=datetime(2024, 1, 15),
        metadata={"source": "Sentinel-1", "resolution_m": 20, "polarization": "VV"},
    ),
}


def get_raster_path(resource_type: ResourceType, base_path: str = "/data/rasters") -> str:
    """Obtiene path completo del raster para un tipo de recurso."""
    source = RASTER_CATALOG.get(resource_type)
    if not source:
        raise ValueError(f"Tipo de recurso no válido: {resource_type}")
    import os
    env_path = os.getenv(f"RASTER_PATH_{resource_type.upper()}")
    if env_path:
        return env_path
    return source.path.replace("/data/rasters", base_path)


def get_raster_source(resource_type: ResourceType) -> RasterSource:
    """Obtiene configuración completa del raster."""
    source = RASTER_CATALOG.get(resource_type)
    if not source:
        raise ValueError(f"Tipo de recurso no válido: {resource_type}")
    return source


def get_raster_version(resource_type: ResourceType) -> str:
    """Obtiene la versión del raster."""
    return RASTER_CATALOG[resource_type].version


def get_raster_date(resource_type: ResourceType) -> datetime:
    """Obtiene la fecha del raster."""
    return RASTER_CATALOG[resource_type].date