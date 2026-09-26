# Schemas de análisis - Pydantic
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
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