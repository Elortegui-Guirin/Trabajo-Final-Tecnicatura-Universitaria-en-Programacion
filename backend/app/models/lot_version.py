# Modelo de versión de lote - Historial de geometrías
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, func, ForeignKey
from geoalchemy2 import Geometry
from datetime import datetime, timezone
from uuid import UUID


class LotVersion(SQLModel, table=True):
    """
    Historial de versiones de geometría de un lote.
    Permite trazabilidad completa de cambios geométricos.
    """
    __tablename__ = "lot_versions"
    
    id: UUID = Field(default=None, primary_key=True)
    lot_id: UUID = Field(foreign_key="lots.id", nullable=False)
    version_number: int = Field(nullable=False)  # 1, 2, 3... incremental
    name: str = Field(nullable=False)
    area_ha: float = Field(nullable=False)
    geometry: str = Field(
        sa_column=Column(Geometry("POLYGON", srid=4326), nullable=False)
    )
    changed_by: UUID = Field(foreign_key="users.id", nullable=False)  # Usuario que hizo el cambio
    change_reason: str | None = Field(default=None)  # Motivo opcional del cambio
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )