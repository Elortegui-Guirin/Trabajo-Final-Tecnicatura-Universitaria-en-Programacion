# Schemas de análisis - Pydantic
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID


class ResourceTypeEnum(str):
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


class AnalysisListResponse(BaseModel):
    items: List[AnalysisRead]
    total: int
    page: int
    size: int


class TimeSeriesPoint(BaseModel):
    analyzed_at: datetime
    average_rate: float
    resource_type: ResourceTypeEnum


class TimeSeriesResponse(BaseModel):
    lot_id: UUID
    resource_type: ResourceTypeEnum
    data: List[TimeSeriesPoint]


# === Nuevos schemas para mejoras ===

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