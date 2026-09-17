# Endpoints de lotes - FastAPI
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemas.lot import LotCreate, LotUpdate, LotRead, LotListResponse
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
    """Crea un nuevo lote con geometría GeoJSON."""
    lot = await lot_service.create_lot(
        session=session,
        user_id=current_user.id,
        name=lot_data.name,
        geometry=lot_data.geometry.model_dump(),
    )
    return await lot_service.lot_to_read(lot)


@router.get("", response_model=LotListResponse)
async def list_lots(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> LotListResponse:
    """Lista lotes del usuario autenticado con paginación y búsqueda."""
    lots, total = await lot_service.get_lots(
        session=session,
        user_id=current_user.id,
        page=page,
        size=size,
        search=search,
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


@router.patch("/{lot_id}", response_model=LotRead)
async def update_lot(
    lot_id: UUID,
    lot_data: LotUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> LotRead:
    """Actualiza nombre y/o geometría de un lote."""
    lot = await lot_service.update_lot(
        session=session,
        lot_id=lot_id,
        user_id=current_user.id,
        name=lot_data.name,
        geometry=lot_data.geometry.model_dump() if lot_data.geometry else None,
    )
    if not lot:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    return await lot_service.lot_to_read(lot)


@router.delete("/{lot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lot(
    lot_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Elimina un lote (cascada elimina analyses asociados)."""
    deleted = await lot_service.delete_lot(session, lot_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Lote no encontrado")