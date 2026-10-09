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

    @property
    def vertex_count(self) -> int:
        """Total vértices en el anillo exterior (excluyendo cierre)."""
        if self.coordinates and len(self.coordinates) > 0:
            return len(self.coordinates[0]) - 1  # -1 porque primer==último
        return 0


class GeometryValidationResult(BaseModel):
    valid: bool = True
    errors: List[str] = []
    fixed_geometry: Optional["GeoJSONPolygon"] = None
    area_ha: Optional[float] = None
    warnings: List[str] = []


# Constantes de validación
MAX_VERTICES = 5000
MIN_AREA_HA = 0.01  # 100 m²
MAX_AREA_HA = 10000  # 10,000 ha


class GeometryValidationConfig(BaseModel):
    """Configuración de validación geométrica."""
    max_vertices: int = MAX_VERTICES
    min_area_ha: float = MIN_AREA_HA
    max_area_ha: float = MAX_AREA_HA
    simplify_tolerance: float = 0.00001  # ~1m en WGS84
    reject_multipolygon: bool = True