# Celery Tasks para análisis raster con cache, concurrencia y versionado
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, and_
from uuid import UUID
from datetime import datetime, timezone
import hashlib
import logging

from app.db.database import async_session_maker
from app.models.lot import Lot
from app.models.analysis import Analysis, ResourceType, AnalysisStatus
from app.services import raster_service
from app.core.config import get_settings
from app.schemas.analysis import ConcurrentAnalysisError

logger = logging.getLogger(__name__)
settings = get_settings()


def _compute_geometry_hash(geometry: dict) -> str:
    """Calcula SHA256 de la geometría para cache."""
    import json
    geom_str = json.dumps(geometry, sort_keys=True)
    return hashlib.sha256(geom_str.encode()).hexdigest()


def _check_concurrent_analysis(session: AsyncSession, lot_id: UUID, resource_type: ResourceType) -> Optional[Analysis]:
    """Verifica si ya hay un análisis en curso para este lote y recurso."""
    stmt = select(Analysis).where(
        and_(
            Analysis.lot_id == lot_id,
            Analysis.resource_type == resource_type,
            Analysis.status.in_([AnalysisStatus.PENDING, AnalysisStatus.PROCESSING])
        )
    )
    result = session.exec(stmt)
    return result.first()


def _check_cache(session: AsyncSession, lot_id: UUID, resource_type: ResourceType, geometry_hash: str, raster_version: str) -> Optional[Analysis]:
    """Verifica si ya existe un análisis completado con los mismos parámetros."""
    stmt = select(Analysis).where(
        and_(
            Analysis.lot_id == lot_id,
            Analysis.resource_type == resource_type,
            Analysis.lot_geometry_hash == geometry_hash,
            Analysis.raster_version == raster_version,
            Analysis.status == AnalysisStatus.COMPLETED,
        )
    ).order_by(Analysis.analyzed_at.desc())
    
    result = session.exec(stmt)
    return result.first()


@shared_task(bind=True, max_retries=3, default_retry_delay=60, acks_late=True)
def run_analysis_task(self, analysis_id: str):
    """
    Task Celery para ejecutar análisis raster en background con:
    - Cache: evita re-ejecutar si ya existe análisis con misma geometría+raster_version
    - Concurrencia: evita análisis simultáneos del mismo lote+recurso
    - Versionado: guarda raster_version y raster_date
    - Almacenamiento configurable: store_clipped_raster
    """
    import asyncio
    import json
    
    async def _run():
        async with async_session_maker() as session:
            try:
                # Obtener análisis
                stmt = select(Analysis).where(Analysis.id == UUID(analysis_id))
                result = await session.exec(stmt)
                analysis = result.first()
                
                if not analysis:
                    raise ValueError(f"Análisis {analysis_id} no encontrado")
                
                # === CONTROL DE CONCURRENCIA ===
                existing = _check_concurrent_analysis(session, analysis.lot_id, ResourceType(analysis.resource_type))
                if existing and existing.id != analysis.id:
                    # Ya hay otro análisis en curso para este lote+recurso
                    raise ConcurrentAnalysisError(
                        existing_analysis_id=existing.id,
                        existing_status=existing.status,
                        retry_after_seconds=30
                    )
                
                # Obtener lote y geometría
                stmt = select(Lot).where(Lot.id == analysis.lot_id)
                result = await session.exec(stmt)
                lot = result.first()
                
                if not lot:
                    raise ValueError(f"Lote {analysis.lot_id} no encontrado")
                
                # === CACHE: Verificar si ya existe análisis idéntico ===
                from geoalchemy2.shape import to_shape
                from shapely.geometry import mapping
                lot_geom = to_shape(lot.geometry)
                geom_geojson = mapping(lot_geom)
                geometry_hash = _compute_geometry_hash(geom_geojson)
                raster_version = raster_service.get_raster_version(ResourceType(analysis.resource_type))
                
                cached = _check_cache(session, analysis.lot_id, ResourceType(analysis.resource_type), geometry_hash, raster_version)
                if cached:
                    # Ya existe análisis idéntico completado -> copiar resultados
                    logger.info(f"Cache hit para análisis {analysis_id}, usando resultado de {cached.id}")
                    analysis.average_rate = cached.average_rate
                    analysis.min_value = cached.min_value
                    analysis.max_value = cached.max_value
                    analysis.std_dev = cached.std_dev
                    analysis.percentiles = cached.percentiles
                    analysis.raster_version = cached.raster_version
                    analysis.raster_date = cached.raster_date
                    analysis.lot_geometry_hash = cached.lot_geometry_hash
                    analysis.clipped_raster_path = cached.clipped_raster_path
                    analysis.store_clipped_raster = cached.store_clipped_raster
                    analysis.status = AnalysisStatus.COMPLETED
                    analysis.analyzed_at = datetime.now(timezone.utc)
                    await session.commit()
                    return {"cached": True, "analysis_id": str(cached.id)}
                
                # Guardar hash de geometría
                analysis.lot_geometry_hash = geometry_hash
                analysis.raster_version = raster_version
                analysis.raster_date = raster_service.get_raster_date(ResourceType(analysis.resource_type))
                
                # Marcar como processing
                analysis.status = AnalysisStatus.PROCESSING
                await session.commit()
                
                # Ejecutar análisis
                resource_type = ResourceType(analysis.resource_type)
                completed = await raster_service.analyze_lot_resource(
                    session=session,
                    lot_id=analysis.lot_id,
                    resource_type=resource_type,
                    base_raster_path=settings.RASTER_DATA_PATH,
                    store_clipped=analysis.store_clipped_raster,
                )
                
                # Actualizar con resultados
                analysis.average_rate = completed.average_rate
                analysis.min_value = completed.min_value
                analysis.max_value = completed.max_value
                analysis.std_dev = completed.std_dev
                analysis.percentiles = completed.percentiles
                analysis.raster_file_reference = completed.raster_file_reference
                analysis.raster_version = raster_version
                analysis.raster_date = raster_service.get_raster_date(ResourceType(analysis.resource_type))
                analysis.status = AnalysisStatus.COMPLETED
                analysis.analyzed_at = datetime.now(timezone.utc)
                analysis.error_message = None
                
                await session.commit()
                logger.info(f"Análisis completado: {analysis.id}, tasa={completed.average_rate:.4f}")
                return {"cached": False, "analysis_id": str(analysis.id)}
                
            except ConcurrentAnalysisError:
                raise
            except Exception as e:
                logger.error(f"Análisis {analysis_id} falló: {e}")
                # Marcar como failed
                stmt = select(Analysis).where(Analysis.id == UUID(analysis_id))
                result = await session.exec(stmt)
                analysis = result.first()
                if analysis:
                    analysis.status = AnalysisStatus.FAILED
                    analysis.error_message = str(e)
                    await session.commit()
                raise
    
    try:
        return asyncio.run(_run())
    except ConcurrentAnalysisError as e:
        # Re-lanzar con info para el cliente
        raise self.retry(exc=e, countdown=30, max_retries=3)
    except Exception as e:
        logger.error(f"Análisis {analysis_id} falló: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


def _compute_geometry_hash(geometry: dict) -> str:
    """Calcula SHA256 de la geometría para cache."""
    import json
    geom_str = json.dumps(geometry, sort_keys=True)
    return hashlib.sha256(geom_str.encode()).hexdigest()


# Importar hashlib aquí para evitar import circular
import hashlib


@shared_task
def check_analysis_cache(lot_id: str, resource_type: str, geometry_hash: str, raster_version: str) -> dict:
    """
    Task síncrona para verificar cache antes de crear análisis.
    Retorna: {"cached": bool, "analysis": AnalysisRead|None, "message": str}
    """
    import asyncio
    
    async def _check():
        async with async_session_maker() as session:
            from sqlmodel import select, and_
            from app.models.analysis import Analysis, AnalysisStatus, ResourceType
            
            stmt = select(Analysis).where(
                and_(
                    Analysis.lot_id == UUID(lot_id),
                    Analysis.resource_type == ResourceType(resource_type),
                    Analysis.lot_geometry_hash == geometry_hash,
                    Analysis.raster_version == raster_version,
                    Analysis.status == AnalysisStatus.COMPLETED,
                )
            ).order_by(Analysis.analyzed_at.desc())
            
            result = await session.exec(stmt)
            cached = result.first()
            
            if cached:
                from app.schemas.analysis import AnalysisRead
                return {
                    "cached": True,
                    "analysis": AnalysisRead.model_validate(cached),
                    "message": f"Análisis encontrado en cache (ID: {cached.id})"
                }
            return {"cached": False, "analysis": None, "message": "No hay análisis en cache"}
    
    return asyncio.run(_check())


@shared_task
def update_all_raster_layers() -> dict:
    """
    Task programada: actualizar todas las capas raster desde fuente origen.
    Ejecutar diariamente via Celery Beat.
    """
    logger.info("Iniciando actualización programada de capas raster...")
    # TODO: Implementar lógica real de actualización
    # 1. Conectar a Google Earth Engine / Sentinel Hub / NASA
    # 2. Descargar nuevas imágenes
    # 3. Procesar y generar GeoTIFF actualizados
    # 4. Reemplazar archivos en /data/rasters/
    # 5. Actualizar versiones en RASTER_CATALOG
    # 6. Opcional: re-analizar lotes afectados
    logger.info("Actualización de capas raster completada (placeholder)")
    return {"status": "completed", "message": "Actualización de capas raster completada"}


@shared_task
def generate_alerts_for_anomalies() -> dict:
    """
    Detectar anomalías en análisis recientes y generar alertas.
    """
    import asyncio
    
    async def _check():
        async with async_session_maker() as session:
            from sqlmodel import select, and_
            from app.models.analysis import Analysis, AnalysisStatus
            from app.models.lot import Lot
            
            # Buscar análisis recientes completados (últimas 24h)
            cutoff = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
            stmt = (
                select(Analysis)
                .where(
                    Analysis.status == AnalysisStatus.COMPLETED,
                    Analysis.analyzed_at >= cutoff,
                )
            )
            result = await session.exec(stmt)
            recent = result.all()
            
            alerts = []
            for analysis in recent:
                # Lógica de detección de anomalías
                # Ejemplo: tasa < 10% del promedio histórico -> alerta
                pass
            
            return {"alerts_generated": len(alerts), "analyzed": len(recent)}
    
    return asyncio.run(_check())


@shared_task
def generate_analysis_report(analysis_id: str, config: dict = None) -> dict:
    """
    Genera reporte PDF del análisis.
    """
    import asyncio
    
    async def _generate():
        async with async_session_maker() as session:
            from sqlmodel import select
            from app.models.analysis import Analysis
            from app.models.lot import Lot
            from app.models.user import User
            
            stmt = select(Analysis).where(Analysis.id == UUID(analysis_id))
            result = await session.exec(stmt)
            analysis = result.first()
            
            if not analysis:
                raise ValueError(f"Análisis {analysis_id} no encontrado")
            
            # Obtener lote y usuario
            lot_stmt = select(Lot).where(Lot.id == analysis.lot_id)
            lot_result = await session.exec(lot_stmt)
            lot = lot_result.first()
            
            user_stmt = select(User).where(User.id == lot.user_id)
            user_result = await session.exec(user_stmt)
            user = user_result.first()
            
            # TODO: Generar PDF con WeasyPrint/ReportLab
            # Contenido:
            # - Logo
            # - Metadatos (usuario, lote, fecha)
            # - Parámetros (recurso, raster_version, raster_date)
            # - Estadísticas (media, min, max, std, percentiles)
            # - Leyenda
            # - Mapa del lote (embebido)
            
            report_path = f"/data/reports/analysis_{analysis_id}.pdf"
            # generate_pdf(...) -> report_path
            
            return {
                "report_id": str(UUID(int=0)),  # placeholder
                "analysis_id": analysis_id,
                "pdf_url": f"/api/reports/analysis_{analysis_id}.pdf",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
    
    return asyncio.run(_generate())