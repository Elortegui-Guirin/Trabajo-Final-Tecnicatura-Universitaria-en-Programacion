# Configuración de catálogo raster
from typing import Dict, Optional
from pydantic import BaseModel
from enum import Enum


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


# Catálogo de recursos forrajeros
# En producción, estos paths vienen de variable de entorno RASTER_DATA_PATH
RASTER_CATALOG: Dict[ResourceType, RasterSource] = {
    ResourceType.RESOURCE_1: RasterSource(
        path="/data/rasters/resource_1.tif",
        band=1,
        nodata=-9999,
        description="Biomasa verde (kg/ha)",
    ),
    ResourceType.RESOURCE_2: RasterSource(
        path="/data/rasters/resource_2.tif",
        band=1,
        nodata=-9999,
        description="Cobertura suelo (%)",
    ),
    ResourceType.RESOURCE_3: RasterSource(
        path="/data/rasters/resource_3.tif",
        band=1,
        nodata=-9999,
        description="Índice de vegetación (NDVI/EVI)",
    ),
    ResourceType.RESOURCE_4: RasterSource(
        path="/data/rasters/resource_4.tif",
        band=1,
        nodata=-9999,
        description="Humedad suelo (%)",
    ),
}


def get_raster_path(resource_type: ResourceType, base_path: str = "/data/rasters") -> str:
    """Obtiene path completo del raster para un tipo de recurso."""
    source = RASTER_CATALOG.get(resource_type)
    if not source:
        raise ValueError(f"Tipo de recurso no válido: {resource_type}")
    # Permitir override por variable de entorno
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