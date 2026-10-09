# Modelo de datos Analysis - SQLModel
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, func, ForeignKey, Enum as SAEnum, Text, Index
from datetime import datetime
from uuid import UUID
from typing import Optional
import enum


class ResourceType(str, enum.Enum):
    RESOURCE_1 = "resource_1"
    RESOURCE_2 = "resource_2"
    RESOURCE_3 = "resource_3"
    RESOURCE_4 = "resource_4"


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Analysis(SQLModel, table=True):
    __tablename__ = "analyses"
    
    id: UUID = Field(default=None, primary_key=True)
    lot_id: UUID = Field(foreign_key="lots.id", nullable=False)
    resource_type: ResourceType = Field(
        sa_column=Column(SAEnum(ResourceType), nullable=False)
    )
    average_rate: float = Field(nullable=False)
    min_value: Optional[float] = Field(default=None)
    max_value: Optional[float] = Field(default=None)
    std_dev: Optional[float] = Field(default=None)
    percentiles: Optional[dict] = Field(
        default=None,
        sa_column=Column(Text, nullable=True)  # JSON como texto
    )
    raster_file_reference: str = Field(nullable=False)
    
    # === VERSIONADO DE RASTER ===
    raster_version: str = Field(nullable=False, max_length=100)  # ej: "v2024.1", "v2024.2"
    raster_date: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    
    # === POLÍTICA DE ALMACENAMIENTO ===
    # Si se guarda el raster recortado (opcional, para auditoría)
    clipped_raster_path: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True)
    )
    store_clipped_raster: bool = Field(default=False)  # Políticas: False=solo stats, True=stats+clipped
    
    # === CACHE Y DEDUPLICACIÓN ===
    # Hash de la geometría del lote al momento del análisis (para cache)
    lot_geometry_hash: str = Field(nullable=False, max_length=64)  # SHA256
    
    analyzed_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    status: AnalysisStatus = Field(
        default=AnalysisStatus.PENDING,
        sa_column=Column(SAEnum(AnalysisStatus), nullable=False)
    )
    error_message: Optional[str] = Field(default=None)
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

    # Índices compuestos para consultas frecuentes
    __table_args__ = (
        Index('idx_analyses_lot_resource_status', 'lot_id', 'resource_type', 'status'),
        Index('idx_analyses_geometry_hash', 'lot_geometry_hash'),
        Index('idx_analyses_raster_version', 'raster_version'),
    )


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"