# Configuración de catálogo raster con versionado
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

# Un único enum de recursos para toda la app (el mismo que usa el modelo Analysis)
from app.models.analysis import ResourceType


class RasterSource(BaseModel):
    path: str
    band: int = 1
    nodata: Optional[float] = None
    description: str = ""
    crs: Optional[str] = None  # Si None, se detecta del archivo
    
    # === VERSIONADO ===
    version: str = Field(default="v1.0.0", description="Versión del raster (ej: v2024.1, v2024.2)")
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Fecha del raster")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales")


# Catálogo de recursos forrajeros con versionado
# Fecha de los mapas de tasa de crecimiento cargados actualmente
_FECHA_MAPAS = datetime(2026, 10, 31, tzinfo=timezone.utc)
_VERSION_MAPAS = "v2026.10.31"
_UNIDAD = "kg MS/ha/día"

# Catálogo de recursos forrajeros: un GeoTIFF de tasa de crecimiento por especie.
# Los IDs internos (resource_1..4) se mantienen para no tocar la base de datos.
# nodata=None -> se usa el NoData definido en cada archivo .tif.
# Cuando haya mapas de otra fecha: actualizar _FECHA_MAPAS y _VERSION_MAPAS
# (los análisis viejos quedan guardados con su versión y fecha).
RASTER_CATALOG: Dict[ResourceType, RasterSource] = {
    ResourceType.RESOURCE_1: RasterSource(
        path="/data/rasters/alfalfa.tif",
        band=1,
        nodata=None,
        description=f"Alfalfa - tasa de crecimiento ({_UNIDAD})",
        version=_VERSION_MAPAS,
        date=_FECHA_MAPAS,
        metadata={"especie": "Alfalfa", "variable": "tasa de crecimiento", "unidad": _UNIDAD},
    ),
    ResourceType.RESOURCE_2: RasterSource(
        path="/data/rasters/festuca.tif",
        band=1,
        nodata=None,
        description=f"Festuca - tasa de crecimiento ({_UNIDAD})",
        version=_VERSION_MAPAS,
        date=_FECHA_MAPAS,
        metadata={"especie": "Festuca", "variable": "tasa de crecimiento", "unidad": _UNIDAD},
    ),
    ResourceType.RESOURCE_3: RasterSource(
        path="/data/rasters/raigras.tif",
        band=1,
        nodata=None,
        description=f"Raigrás - tasa de crecimiento ({_UNIDAD})",
        version=_VERSION_MAPAS,
        date=_FECHA_MAPAS,
        metadata={"especie": "Raigrás", "variable": "tasa de crecimiento", "unidad": _UNIDAD},
    ),
    ResourceType.RESOURCE_4: RasterSource(
        path="/data/rasters/pastizal.tif",
        band=1,
        nodata=None,
        description=f"Pastizal natural - tasa de crecimiento ({_UNIDAD})",
        version=_VERSION_MAPAS,
        date=_FECHA_MAPAS,
        metadata={"especie": "Pastizal natural", "variable": "tasa de crecimiento", "unidad": _UNIDAD},
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