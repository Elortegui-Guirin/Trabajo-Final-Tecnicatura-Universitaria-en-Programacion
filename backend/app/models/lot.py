# Modelo de datos Lot - SQLModel
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, func, ForeignKey
from geoalchemy2 import Geometry
from datetime import datetime, timezone
from uuid import UUID


class Lot(SQLModel, table=True):
    __tablename__ = "lots"
    
    id: UUID = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False)
    name: str = Field(sa_column=Column(None, nullable=False))
    area_ha: float = Field(sa_column=Column(None, nullable=False))
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