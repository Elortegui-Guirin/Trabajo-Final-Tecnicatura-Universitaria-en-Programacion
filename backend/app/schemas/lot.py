# Schemas de lotes - Pydantic
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class GeometryInput(BaseModel):
    type: str = Field(default="Polygon", pattern="^Polygon$")
    coordinates: List[List[List[float]]]  # [exterior_ring, interior_ring*]


class LotCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    geometry: GeometryInput


class LotUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    geometry: Optional[GeometryInput] = None


class LotRead(BaseModel):
    id: UUID
    name: str
    area_ha: float
    geometry: dict  # GeoJSON
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LotListResponse(BaseModel):
    items: List[LotRead]
    total: int
    page: int
    size: int