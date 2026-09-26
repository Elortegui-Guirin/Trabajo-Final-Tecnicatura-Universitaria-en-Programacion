# Endpoints de análisis - FastAPI
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemas.analysis import (
    AnalysisCreate, AnalysisRead, AnalysisListResponse, TimeSeriesResponse, ResourceTypeEnum
)
from app.models.user import User
from app.db.database import get_session
from app.api.deps import get_current_active_user
from app.services import raster_service

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("", response_model=AnalysisRead, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis(
    analysis_data: AnalysisCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> AnalysisRead:
    """
    Inicia análisis asíncrono de un lote.
    Retorna analysis_id con status=pending; el background task lo procesa.
    """
    # Verificar que el lote pertenece al usuario
    from app.models.lot import Lot
    from sqlmodel import select
    stmt = select(Lot).where(Lot.id == analysis_data.lot_id, Lot.user_id == current_user.id)
    result = await session.exec(stmt)
    lot = result.first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lote no encontrado o sin permisos")
    
    # Crear análisis en estado pending
    analysis = Analysis(
        lot_id=analysis_data.lot_id,
        resource_type=analysis_data.resource_type.value,
        average_rate=0.0,  # placeholder
        raster_file_reference="",
        status="pending",
    )
    session.add(analysis)
    await session.commit()
    await session.refresh(analysis)
    
    # Programar task en background
    background_tasks.add_task(
        raster_service.run_analysis_task,
        session=session,
        analysis_id=analysis.id,
    )
    
    return AnalysisRead.model_validate(analysis)


@router.get("", response_model=AnalysisListResponse)
async def list_analyses(
    lot_id: Optional[UUID] = Query(None),
    resource_type: Optional[ResourceTypeEnum] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> AnalysisListResponse:
    """Lista análisis con filtros opcionales (solo del usuario actual via ownership de lote)."""
    from app.models.lot import Lot
    from app.models.analysis import Analysis
    from sqlmodel import select, func
    
    # Subquery para lotes del usuario
    user_lots = select(Lot.id).where(Lot.user_id == current_user.id)
    
    stmt = select(Analysis).where(Analysis.lot_id.in_(user_lots))
    
    if lot_id:
        stmt = stmt.where(Analysis.lot_id == lot_id)
    if resource_type:
        stmt = stmt.where(Analysis.resource_type == resource_type.value)
    
    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.exec(count_stmt)).first()
    
    # Paginación
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Analysis.analyzed_at.desc())
    analyses = (await session.exec(stmt)).all()
    
    items = [AnalysisRead.model_validate(a) for a in analyses]
    return AnalysisListResponse(items=items, total=total, page=page, size=size)


@router.get("/timeseries", response_model=TimeSeriesResponse)
async def get_time_series(
    lot_id: UUID = Query(...),
    resource_type: ResourceTypeEnum = Query(...),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> TimeSeriesResponse:
    """Obtiene serie temporal de análisis para un lote y recurso (gráficos históricos)."""
    from app.models.lot import Lot
    from sqlmodel import select
    
    # Verificar ownership
    stmt = select(Lot).where(Lot.id == lot_id, Lot.user_id == current_user.id)
    result = await session.exec(stmt)
    lot = result.first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    
    data = await raster_service.get_time_series(
        session=session,
        lot_id=lot_id,
        resource_type=ResourceTypeEnum(resource_type.value),
    )
    
    return TimeSeriesResponse(
        lot_id=lot_id,
        resource_type=resource_type,
        data=data,
    )


@router.get("/{analysis_id}", response_model=AnalysisRead)
async def get_analysis(
    analysis_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> AnalysisRead:
    """Obtiene detalle de un análisis."""
    from app.models.lot import Lot
    from app.models.analysis import Analysis
    from sqlmodel import select
    
    stmt = (
        select(Analysis)
        .join(Lot, Analysis.lot_id == Lot.id)
        .where(Analysis.id == analysis_id, Lot.user_id == current_user.id)
    )
    result = await session.exec(stmt)
    analysis = result.first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    
    return AnalysisRead.model_validate(analysis)


@router.get("/lots/{lot_id}/analyses", response_model=AnalysisListResponse)
async def get_lot_analyses(
    lot_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> AnalysisListResponse:
    """Shortcut: análisis de un lote específico."""
    return await list_analyses(
        lot_id=lot_id,
        resource_type=None,
        page=page,
        size=size,
        current_user=current_user,
        session=session,
    )