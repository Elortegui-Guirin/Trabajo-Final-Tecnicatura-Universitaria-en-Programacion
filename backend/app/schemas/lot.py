# Schemas de lotes - Pydantic
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


# Constantes de validación
MIN_AREA_HA = 0.01  # 100 m² mínimo
MAX_AREA_HA = 10000  # 10,000 ha máximo (100 km²)


class GeometryInput(BaseModel):
    type: str = Field(default="Polygon", pattern="^Polygon$")
    coordinates: List[List[List[float]]]  # [exterior_ring, interior_ring*]


class LotCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    geometry: GeometryInput


class LotUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    geometry: Optional[dict] = None
    change_reason: Optional[str] = Field(default=None, max_length=500)


class LotRead(BaseModel):
    id: UUID
    name: str
    area_ha: float
    geometry: dict  # GeoJSON
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LotVersionRead(BaseModel):
    """Versión histórica de un lote."""
    id: UUID
    lot_id: UUID
    version_number: int
    name: str
    area_ha: float
    geometry: dict  # GeoJSON
    changed_by: UUID
    change_reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LotListResponse(BaseModel):
    items: List["LotRead"]
    total: int
    page: int
    size: int


# Parámetros de búsqueda avanzada
class LotSearchParams(BaseModel):
    search: Optional[str] = None  # búsqueda por nombre
    date_from: Optional[datetime] = None  # fecha creación desde
    date_to: Optional[datetime] = None    # fecha creación hasta
    area_min: Optional[float] = Field(default=None, ge=MIN_AREA_HA)
    area_max: Optional[float] = Field(default=None, le=MAX_AREA_HA)
    # Bounding box: [min_lon, min_lat, max_lon, max_lat]
    bbox: Optional[List[float]] = Field(default=None, min_length=4, max_length=4)
    include_deleted: bool = False  # incluir lotes soft-deleted (solo admins)


# Re-export para evitar circular imports
LotListResponse.model_rebuild()