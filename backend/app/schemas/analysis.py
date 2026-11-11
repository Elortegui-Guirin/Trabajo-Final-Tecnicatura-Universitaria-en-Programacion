# Schemas de análisis - Pydantic
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
from uuid import UUID
import json


class ResourceTypeEnum(str, Enum):
    # Tiene que ser un Enum de verdad: el código usa ResourceTypeEnum(...).value
    RESOURCE_1 = "resource_1"
    RESOURCE_2 = "resource_2"
    RESOURCE_3 = "resource_3"
    RESOURCE_4 = "resource_4"


class AnalysisCreate(BaseModel):
    lot_id: UUID
    resource_type: ResourceTypeEnum
    store_clipped_raster: bool = Field(default=False, description="Si almacenar el raster recortado")


class AnalysisRead(BaseModel):
    id: UUID
    lot_id: UUID
    resource_type: ResourceTypeEnum
    average_rate: float
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    std_dev: Optional[float] = None
    percentiles: Optional[Dict[str, float]] = None
    raster_file_reference: str
    raster_version: str
    raster_date: datetime
    clipped_raster_path: Optional[str] = None
    store_clipped_raster: bool
    lot_geometry_hash: str
    analyzed_at: datetime
    status: str  # pending, processing, completed, failed
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}

    @field_validator("status", "resource_type", mode="before")
    @classmethod
    def _enum_as_value(cls, v):
        # El modelo devuelve enums (AnalysisStatus / ResourceType); la API usa el texto
        return v.value if isinstance(v, Enum) else v

    @field_validator("percentiles", mode="before")
    @classmethod
    def _percentiles_as_dict(cls, v):
        # Compatibilidad con filas viejas donde se guardó como texto JSON
        if isinstance(v, str):
            try:
                return json.loads(v)
            except ValueError:
                return None
        return v


class AnalysisListResponse(BaseModel):
    items: List[AnalysisRead]
    total: int
    page: int
    size: int


class TimeSeriesPoint(BaseModel):
    analyzed_at: datetime
    average_rate: float
    resource_type: ResourceTypeEnum
    raster_version: Optional[str] = None
    raster_date: Optional[datetime] = None

    @field_validator("resource_type", mode="before")
    @classmethod
    def _enum_as_value(cls, v):
        return v.value if isinstance(v, Enum) else v


class TimeSeriesResponse(BaseModel):
    lot_id: UUID
    resource_type: ResourceTypeEnum
    data: List[TimeSeriesPoint]


# === Nuevos schemas para mejoras ===

class AnalysisCacheRequest(BaseModel):
    """Body de POST /analyses/check-cache"""
    lot_id: UUID
    resource_type: ResourceTypeEnum


class AnalysisCacheCheck(BaseModel):
    """Respuesta de verificación de cache"""
    cached: bool
    analysis_id: Optional[UUID] = None
    analysis: Optional[AnalysisRead] = None
    message: str


class ConcurrentAnalysisError(BaseModel):
    """Error cuando ya hay un análisis en curso"""
    error: str = "Ya existe un análisis en curso para este lote y recurso"
    existing_analysis_id: UUID
    existing_status: str
    retry_after_seconds: int = 30


class AnalysisReportConfig(BaseModel):
    """Configuración para generación de reporte PDF"""
    include_logo: bool = True
    include_metadata: bool = True
    include_legend: bool = True
    include_analysis_date: bool = True
    include_parameters: bool = True
    logo_path: Optional[str] = None
    title: str = "Reporte de Análisis Forrajero"


class AnalysisReportResponse(BaseModel):
    """Respuesta con reporte PDF generado"""
    report_id: UUID
    analysis_id: UUID
    pdf_url: str
    generated_at: datetime
    expires_at: Optional[datetime] = None


# Constantes para concurrencia
MAX_CONCURRENT_ANALYSES_PER_LOT = 1
ANALYSIS_LOCK_TTL_SECONDS = 300  # 5 minutos