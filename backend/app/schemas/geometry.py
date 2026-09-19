# Schemas compartidos de geometría - Pydantic
from typing import Literal, Optional, List
from pydantic import BaseModel, Field, validator


class GeoJSONPolygon(BaseModel):
    type: Literal["Polygon"] = "Polygon"
    coordinates: List[List[List[float]]]  # [exterior_ring, interior_ring*]

    @validator("coordinates")
    def validate_rings(cls, v):
        if not v or len(v) < 1:
            raise ValueError("Polygon debe tener al menos un anillo exterior")
        if len(v[0]) < 4:
            raise ValueError("Anillo exterior debe tener al menos 4 puntos (primer == último)")
        # Verificar que el primer punto sea igual al último (anillo cerrado)
        if v[0][0] != v[0][-1]:
            raise ValueError("Anillo exterior debe estar cerrado (primer punto == último punto)")
        return v


class GeometryValidationResult(BaseModel):
    valid: bool = True
    errors: List[str] = []
    fixed_geometry: Optional[GeoJSONPolygon] = None
    area_ha: Optional[float] = None
    warnings: List[str] = []