# Endpoints de lotes - FastAPI
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemas.lot import (
    LotCreate, LotUpdate, LotRead, LotListResponse, 
    LotVersionRead, LotSearchParams
)
from app.models.user import User
from app.db.database import get_session
from app.api.deps import get_current_active_user
from app.services import lot_service

router = APIRouter(prefix="/lots", tags=["lots"])


@router.post("", response_model=LotRead, status_code=status.HTTP_201_CREATED)
async def create_lot(
    lot_data: LotCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> LotRead:
    """Crea un nuevo lote con geometría GeoJSON. Valida área mínima (0.01 ha)."""
    try:
        lot = await lot_service.create_lot(
            session=session,
            user_id=current_user.id,
            name=lot_data.name,
            geometry=lot_data.geometry.model_dump(),
        )
        return await lot_service.lot_to_read(lot)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("", response_model=LotListResponse)
async def list_lots(
    # Paginación
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    # Búsqueda básica
    search: Optional[str] = Query(None, description="Búsqueda por nombre"),
    # Filtros avanzados
    date_from: Optional[datetime] = Query(None, description="Fecha creación desde (ISO 8601)"),
    date_to: Optional[datetime] = Query(None, description="Fecha creación hasta (ISO 8601)"),
    area_min: Optional[float] = Query(None, ge=0.01, description="Área mínima en hectáreas"),
    area_max: Optional[float] = Query(None, le=10000, description="Área máxima en hectáreas"),
    # Bounding box: min_lon,min_lat,max_lon,max_lat
    bbox: Optional[str] = Query(None, description="Bounding box: min_lon,min_lat,max_lon,max_lat"),
    include_deleted: bool = Query(False, description="Incluir lotes eliminados (solo admins)"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> LotListResponse:
    """Lista lotes del usuario autenticado con paginación y filtros avanzados:
    - Búsqueda por nombre
    - Rango de fechas de creación
    - Rango de área (hectáreas)
    - Bounding box espacial (intersección)
    """
    # Parsear bbox si se proporciona
    bbox_parsed = None
    if bbox:
        try:
            coords = [float(x.strip()) for x in bbox.split(",")]
            if len(coords) != 4:
                raise ValueError
            bbox_parsed = coords
        except ValueError:
            raise HTTPException(
                status_code=422, 
                detail="bbox debe tener formato: min_lon,min_lat,max_lon,max_lat (4 números separados por comas)"
            )
    
    lots, total = await lot_service.get_lots(
        session=session,
        user_id=current_user.id,
        page=page,
        size=size,
        search=search,
        date_from=date_from,
        date_to=date_to,
        area_min=area_min,
        area_max=area_max,
        bbox=bbox_parsed,
        include_deleted=include_deleted,
    )
    items = [await lot_service.lot_to_read(lot) for lot in lots]
    return LotListResponse(items=items, total=total, page=page, size=size)


@router.get("/{lot_id}", response_model=LotRead)
async def get_lot(
    lot_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> LotRead:
    """Obtiene detalle de un lote."""
    lot = await lot_service.get_lot(session, lot_id, current_user.id)
    if not lot:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    return await lot_service.lot_to_read(lot)


@router.get("/{lot_id}/versions", response_model=List[LotVersionRead])
async def get_lot_versions(
    lot_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> List[LotVersionRead]:
    """Obtiene el historial de versiones de geometría de un lote."""
    versions = await lot_service.get_lot_versions(session, lot_id, current_user.id)
    if not versions:
        # Verificar que el lote existe (aunque no tenga versiones)
        lot = await lot_service.get_lot(session, lot_id, current_user.id, include_deleted=True)
        if not lot:
            raise HTTPException(status_code=404, detail="Lote no encontrado")
        return []
    
    result = []
    for v in versions:
        from geoalchemy2.shape import to_shape
        from shapely.geometry import mapping
        geom = to_shape(v.geometry)
        result.append(LotVersionRead(
            id=v.id,
            lot_id=v.lot_id,
            version_number=v.version_number,
            name=v.name,
            area_ha=float(v.area_ha),
            geometry=mapping(geom),
            changed_by=v.changed_by,
            change_reason=v.change_reason,
            created_at=v.created_at,
        ))
    return result


@router.patch("/{lot_id}", response_model=LotRead)
async def update_lot(
    lot_id: UUID,
    lot_data: LotUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> LotRead:
    """Actualiza nombre y/o geometría de un lote. 
    Si cambia la geometría, se crea versión histórica automáticamente.
    Valida área mínima (0.01 ha) en cambios de geometría."""
    try:
        lot = await lot_service.update_lot(
            session=session,
            lot_id=lot_id,
            user_id=current_user.id,
            name=lot_data.name,
            geometry=lot_data.geometry,
            change_reason=lot_data.change_reason,
        )
        if not lot:
            raise HTTPException(status_code=404, detail="Lote no encontrado")
        return await lot_service.lot_to_read(lot)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{lot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lot(
    lot_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Soft delete: marca lote como eliminado (deleted_at). 
    Los analyses históricos se conservan para auditoría."""
    deleted = await lot_service.delete_lot(session, lot_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Lote no encontrado")


@router.post("/{lot_id}/restore", response_model=LotRead)
async def restore_lot(
    lot_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> LotRead:
    """Restaura un lote soft-deleted."""
    restored = await lot_service.restore_lot(session, lot_id, current_user.id)
    if not restored:
        raise HTTPException(status_code=404, detail="Lote no encontrado o no estaba eliminado")
    
    lot = await lot_service.get_lot(session, lot_id, current_user.id, include_deleted=True)
    return await lot_service.lot_to_read(lot)