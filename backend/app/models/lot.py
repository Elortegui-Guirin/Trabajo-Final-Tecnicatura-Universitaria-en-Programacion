# Modelo de datos Lot - SQLModel
from datetime import datetime, timezone
from uuid import UUID, uuid4

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, String, func
from sqlmodel import Column, Field, SQLModel

# Nota: el historial de versiones vive en app/models/lot_version.py (LotVersion).
# Las versiones se crean explícitamente desde app/services/lot_service.py
# (create_lot / update_lot), no con event listeners.


class Lot(SQLModel, table=True):
    __tablename__ = "lots"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    name: str = Field(sa_column=Column(String(255), nullable=False))
    area_ha: float = Field(sa_column=Column(Float, nullable=False))
    geometry: str = Field(
        sa_column=Column(Geometry("POLYGON", srid=4326), nullable=False)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )
    deleted_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
