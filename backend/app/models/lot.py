# Modelo de datos Lot - SQLModel
from sqlmodel import SQLModel, Field, Column, Relationship, Select
from sqlalchemy import DateTime, func, ForeignKey, event
from geoalchemy2 import Geometry
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, List


class LotVersion(SQLModel, table=True):
    """Historial de versiones para un lote."""
    __tablename__ = "lot_versions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    lot_id: UUID = Field(foreign_key="lots.id", nullable=False)
    version_number: int = Field(default=1, ge=1)
    name: str
    area_ha: float
    geometry: str = Field(
        sa_column=Column(Geometry("POLYGON", srid=4326), nullable=False)
    )
    changed_by: UUID
    change_reason: Optional[str] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    
    # Relación hacia atrás al lote padre
    lot: "Lot" = Relationship(back_populates="versions")


class Lot(SQLModel, table=True):
    __tablename__ = "lots"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
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
    deleted_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    
    # Relación hacia el historial de versiones
    versions: List[LotVersion] = Relationship(back_populates="lot", cascade_save=False)


# Event listener para crear versión automáticamente al actualizar un lote
@event.listens_for(Lot, "after_update", call_on_every="SET")
def create_lot_version_on_update(target, connection, target_session=None):
    """Crea una nueva versión cada vez que se actualiza un lote."""
    from datetime import datetime, timezone
    from sqlmodel import select, delete
    
    # Obtener la sesión actual
    session = object.__getattribute__(target, '_session') if hasattr(target, '_session') else None
    
    # Verificar que hubo cambio real en geometría o nombre
    # (En una implementación completa, compararíamos los valores antiguos)
    
    # Crear la versión
    version_number = 1
    # Obtener la última versión existente para este lote
    stmt = select(LotVersion).where(LotVersion.lot_id == target.id).order_by(LotVersion.version_number.desc())
    result = connection.execute(stmt)
    last_version = result.scalar_one_or_none()
    
    if last_version:
        version_number = last_version.version_number + 1
    
    # Crear la nueva versión
    # Note: En una implementación completa, capturaríamos quién hizo el cambio
    # y la razón del cambio desde el contexto de la aplicación
    new_version = LotVersion(
        id=uuid4(),
        lot_id=target.id,
        version_number=version_number,
        name=target.name,
        area_ha=target.area_ha,
        geometry=target.geometry,
        changed_by=target.user_id,  # Usuario que creó/actualizó el lote
        change_reason="Actualización de lote",
    )
    
    connection.add(new_version)