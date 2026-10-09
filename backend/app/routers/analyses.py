# Endpoints de análisis - FastAPI
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemas.analysis import (
    AnalysisCreate, AnalysisRead, AnalysisListResponse, TimeSeriesResponse, 
    ResourceTypeEnum, AnalysisCacheCheck, ConcurrentAnalysisError
)
from app.models.user import User
from app.db.database import get_session
from app.api.deps import get_current_active_user
from app.services import raster_service
from app.workers.raster_tasks import run_analysis_task, check_analysis_cache

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("", response_model=AnalysisRead, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis(
    analysis_data: AnalysisCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> AnalysisRead:
    """
    Inicia análisis asíncrono de un lote (vía Celery).
    Incluye:
    - Verificación de ownership + soft-delete
    - Control de concurrencia (evita análisis simultáneos mismo lote+recurso)
    - Cache: verifica si ya existe análisis idéntico (misma geometría + versión raster)
    - Versionado: guarda raster_version y raster_date
    - Almacenamiento configurable: store_clipped_raster
    Retorna analysis_id con status=pending; Celery task lo procesa.
    """
    from app.models.lot import Lot
    from app.models.analysis import Analysis, ResourceType, AnalysisStatus
    from sqlmodel import select
    from geoalchemy2.shape import to_shape
    from shapely.geometry import mapping
    
    # Verificar que el lote pertenece al usuario (y no está soft-deleted)
    stmt = select(Lot).where(
        Lot.id == analysis_data.lot_id, 
        Lot.user_id == current_user.id,
        Lot.deleted_at.is_(None)
    )
    result = await session.exec(stmt)
    lot = result.first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lote no encontrado o sin permisos")
    
    # Obtener geometría y hash para verificación de cache
    lot_geom = to_shape(lot.geometry)
    geom_geojson = mapping(lot_geom)
    from app.services.raster_service import _compute_geometry_hash
    geometry_hash = _compute_geometry_hash(geom_geojson)
    resource_type = ResourceType(analysis_data.resource_type.value)
    raster_version = raster_service.get_raster_version(resource_type)
    
    # === VERIFICAR CACHE ===
    from app.services.raster_service import _check_cache
    cached = await _check_cache(session, lot.id, resource_type, geometry_hash, raster_version)
    if cached:
        return AnalysisRead.model_validate(cached)
    
    # === CONTROL DE CONCURRENCIA ===
    from app.services.raster_service import _check_concurrent_analysis
    concurrent = _check_concurrent_analysis(session, lot.id, resource_type)
    if concurrent:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Ya existe un análisis en curso para este lote y recurso",
                "existing_analysis_id": str(concurrent.id),
                "existing_status": concurrent.status,
                "retry_after_seconds": 30,
            }
        )
    
    # Crear análisis en estado pending con versionado
    analysis = Analysis(
        lot_id=analysis_data.lot_id,
        resource_type=analysis_data.resource_type.value,
        average_rate=0.0,
        raster_file_reference="",
        status=AnalysisStatus.PENDING.value,
        store_clipped_raster=analysis_data.store_clipped_raster,
        raster_version=raster_service.get_raster_version(resource_type),
        raster_date=raster_service.get_raster_date(resource_type),
        lot_geometry_hash=geometry_hash,
    )
    session.add(analysis)
    await session.commit()
    await session.refresh(analysis)
    
    # Programar task en Celery (no BackgroundTasks)
    run_analysis_task.delay(str(analysis.id))
    
    return AnalysisRead.model_validate(analysis)


@router.post("/check-cache", response_model=dict)
async def check_analysis_cache(
    lot_id: UUID,
    resource_type: ResourceTypeEnum,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Verifica si ya existe un análisis en cache para el lote y recurso dados.
    Útil para el frontend antes de iniciar un nuevo análisis.
    """
    from app.models.lot import Lot
    from app.models.analysis import ResourceType
    from sqlmodel import select
    from geoalchemy2.shape import to_shape
    from shapely.geometry import mapping
    from app.services.raster_service import _compute_geometry_hash
    
    # Verificar ownership
    stmt = select(Lot).where(Lot.id == lot_id, Lot.user_id == current_user.id, Lot.deleted_at.is_(None))
    result = await session.exec(stmt)
    lot = result.first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    
    # Calcular hash de geometría
    lot_geom = to_shape(lot.geometry)
    geom_geojson = mapping(lot_geom)
    from app.services.raster_service import _compute_geometry_hash
    geometry_hash = _compute_geometry_hash(geom_geojson)
    
    resource_type = ResourceType(resource_type.value)
    raster_version = raster_service.get_raster_version(resource_type)
    
    # Verificar cache
    cached = await _check_cache(session, lot.id, resource_type, geometry_hash, raster_version)
    
    if cached:
        return {
            "cached": True,
            "analysis": AnalysisRead.model_validate(cached),
            "message": f"Análisis encontrado en cache (ID: {cached.id})"
        }
    
    return {
        "cached": False,
        "analysis": None,
        "message": "No hay análisis en cache para estos parámetros"
    }


@router.get("", response_model=AnalysisListResponse)
async def list_analyses(
    lot_id: Optional[UUID] = Query(None),
    resource_type: Optional[ResourceTypeEnum] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> AnalysisListResponse:
    """Lista análisis con filtros opcionales (solo del usuario actual via ownership de lote)."""
    from app.models.lot import Lot
    from app.models.analysis import Analysis, AnalysisStatus
    from sqlmodel import select, func
    
    # Subquery para lotes del usuario (solo activos)
    user_lots = select(Lot.id).where(Lot.user_id == current_user.id, Lot.deleted_at.is_(None))
    
    stmt = select(Analysis).where(Analysis.lot_id.in_(user_lots))
    
    if lot_id:
        stmt = stmt.where(Analysis.lot_id == lot_id)
    if resource_type:
        stmt = stmt.where(Analysis.resource_type == resource_type.value)
    if status:
        stmt = stmt.where(Analysis.status == status)
    
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
    """Obtiene serie temporal de análisis para un lote y recurso (gráficos históricos).
    Incluye raster_version y raster_date para cada punto."""
    from app.models.lot import Lot
    from sqlmodel import select
    
    stmt = select(Lot).where(
        Lot.id == lot_id, 
        Lot.user_id == current_user.id,
        Lot.deleted_at.is_(None)
    )
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
    """Obtiene detalle de un análisis con información completa de versionado."""
    from app.models.lot import Lot
    from app.models.analysis import Analysis
    from sqlmodel import select
    
    stmt = (
        select(Analysis)
        .join(Lot, Analysis.lot_id == Lot.id)
        .where(
            Analysis.id == analysis_id, 
            Lot.user_id == current_user.id,
            Lot.deleted_at.is_(None)
        )
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
    from app.models.lot import Lot
    from sqlmodel import select
    
    # Verificar ownership
    stmt = select(Lot).where(Lot.id == lot_id, Lot.user_id == current_user.id, Lot.deleted_at.is_(None))
    result = await session.exec(stmt)
    lot = result.first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    
    return await list_analyses(
        lot_id=lot_id,
        resource_type=None,
        page=page,
        size=size,
        current_user=current_user,
        session=session,
    )


@router.post("/{analysis_id}/report", response_model=dict)
async def generate_analysis_report(
    analysis_id: UUID,
    config: Optional[dict] = None,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Genera reporte PDF del análisis.
    """
    from app.models.lot import Lot
    from app.models.analysis import Analysis
    from app.models.user import User
    from sqlmodel import select
    from app.utils.report_generator import generate_analysis_report_pdf
    
    # Verificar ownership
    stmt = (
        select(Analysis)
        .join(Lot, Analysis.lot_id == Lot.id)
        .where(Analysis.id == analysis_id, Lot.user_id == current_user.id, Lot.deleted_at.is_(None))
    )
    result = await session.exec(stmt)
    analysis = result.first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    
    # Obtener lote y usuario
    lot = await session.get(Lot, analysis.lot_id)
    user = await session.get(User, current_user.id)
    
    # Preparar datos
    analysis_data = {
        "id": str(analysis.id),
        "resource_type": analysis.resource_type,
        "average_rate": analysis.average_rate,
        "min_value": analysis.min_value,
        "max_value": analysis.max_value,
        "std_dev": analysis.std_dev,
        "percentiles": analysis.percentiles,
        "raster_file_reference": analysis.raster_file_reference,
        "raster_version": analysis.raster_version,
        "raster_date": analysis.raster_date,
        "store_clipped_raster": analysis.store_clipped_raster,
        "clipped_raster_path": analysis.clipped_raster_path,
    }
    
    lot_data = {
        "id": str(lot.id),
        "name": lot.name,
        "area_ha": lot.area_ha,
        "geometry": lot.geometry,  # se serializa en report_generator
    }
    
    user_data = {
        "id": str(user.id),
        "full_name": user.full_name,
        "email": user.email,
    }
    
    # Generar PDF
    pdf_path = generate_analysis_report_pdf(analysis_data, lot_data, user_data, config)
    
    return {
        "report_id": str(UUID(int=0)),  # placeholder
        "analysis_id": str(analysis_id),
        "pdf_url": f"/api/reports/{Path(pdf_path).name}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }