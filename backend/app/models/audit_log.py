# Modelo de Auditoría - SQLModel (Evolución futura: trazabilidad de cambios)
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, func, ForeignKey, Text
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional


class AuditLog(SQLModel, table=True):
    """
    Registro de auditoría para trazabilidad de cambios.
    Evolución futura: no implementado en MVP, preparado para activar.
    """
    __tablename__ = "audit_log"
    
    id: UUID = Field(default=None, primary_key=True)
    table_name: str = Field(nullable=False)
    record_id: str = Field(nullable=False)  # UUID como string para flexibilidad
    action: str = Field(nullable=False)  # INSERT, UPDATE, DELETE
    old_values: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))  # JSON
    new_values: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))  # JSON
    user_id: Optional[str] = Field(default=None)  # Quién hizo el cambio
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )