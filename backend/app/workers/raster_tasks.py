# Tasks Celery para análisis raster
import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID

from celery import shared_task
from sqlmodel import and_, select

from app.core.config import get_settings
from app.db.database import make_worker_session_maker
from app.models.analysis import Analysis, AnalysisStatus, ResourceType
from app.models.lot import Lot
from app.models.user import User
from app.services import raster_service

logger = logging.getLogger(__name__)
settings = get_settings()


def _run_with_session(work):
    """
    Ejecuta `work(session)` (una corrutina) en un event loop nuevo con su propio engine.
    Celery corre las tasks de forma síncrona, por eso cada una usa asyncio.run()
    y un engine con NullPool (las conexiones de asyncpg no se pueden compartir entre loops).
    """
    async def _main():
        engine, session_maker = make_worker_session_maker()
        try:
            async with session_maker() as session:
                return await work(session)
        finally:
            await engine.dispose()

    return asyncio.run(_main())


@shared_task(bind=True, acks_late=True)
def run_analysis_task(self, analysis_id: str):
    """
    Task Celery: toma el análisis en estado pending creado por POST /analyses,
    lo pasa a processing, recorta el raster al lote, calcula estadísticas y
    guarda los resultados en ESE MISMO registro (status=completed).
    Si algo falla (ej: falta el .tif o el lote está fuera del raster) queda status=failed
    con el error en error_message. No se reintenta: un archivo faltante no se arregla solo.
    """
    async def work(session):
        analysis = await raster_service.run_analysis_task(
            session=session,
            analysis_id=UUID(analysis_id),
            base_raster_path=settings.RASTER_DATA_PATH,
        )
        logger.info(f"Análisis completado: {analysis.id}, tasa={analysis.average_rate:.4f}")
        return {"analysis_id": str(analysis.id), "status": "completed"}

    try:
        return _run_with_session(work)
    except Exception as e:
        # raster_service.run_analysis_task ya marcó el análisis como failed
        logger.error(f"Análisis {analysis_id} falló: {e}")
        return {"analysis_id": analysis_id, "status": "failed", "error": str(e)}


@shared_task
def check_analysis_cache(lot_id: str, resource_type: str, geometry_hash: str, raster_version: str) -> dict:
    """
    Verifica cache fuera del request (uso opcional desde otras tasks).
    El endpoint POST /analyses/check-cache hace esta misma consulta directamente.
    """
    async def work(session):
        stmt = select(Analysis).where(
            and_(
                Analysis.lot_id == UUID(lot_id),
                Analysis.resource_type == ResourceType(resource_type),
                Analysis.lot_geometry_hash == geometry_hash,
                Analysis.raster_version == raster_version,
                Analysis.status == AnalysisStatus.COMPLETED,
            )
        ).order_by(Analysis.analyzed_at.desc())
        cached = (await session.exec(stmt)).first()
        if cached:
            return {
                "cached": True,
                "analysis_id": str(cached.id),
                "message": f"Análisis encontrado en cache (ID: {cached.id})",
            }
        return {"cached": False, "analysis_id": None, "message": "No hay análisis en cache"}

    return _run_with_session(work)


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
    async def work(session):
        # Buscar análisis completados desde el inicio del día (UTC)
        cutoff = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = select(Analysis).where(
            Analysis.status == AnalysisStatus.COMPLETED,
            Analysis.analyzed_at >= cutoff,
        )
        recent = (await session.exec(stmt)).all()

        alerts = []
        for _analysis in recent:
            # TODO: lógica de detección de anomalías
            # Ejemplo: tasa < 10% del promedio histórico -> alerta
            pass

        return {"alerts_generated": len(alerts), "analyzed": len(recent)}

    return _run_with_session(work)


@shared_task
def generate_analysis_report(analysis_id: str, config: dict = None) -> dict:
    """
    Genera reporte PDF del análisis (en background).
    """
    async def work(session):
        analysis = (await session.exec(select(Analysis).where(Analysis.id == UUID(analysis_id)))).first()
        if not analysis:
            raise ValueError(f"Análisis {analysis_id} no encontrado")

        lot = (await session.exec(select(Lot).where(Lot.id == analysis.lot_id))).first()
        user = (await session.exec(select(User).where(User.id == lot.user_id))).first() if lot else None  # noqa: F841

        # TODO: Generar PDF con app.utils.report_generator.generate_analysis_report_pdf
        return {
            "report_id": str(UUID(int=0)),  # placeholder
            "analysis_id": analysis_id,
            "pdf_url": f"/api/reports/analysis_{analysis_id}.pdf",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    return _run_with_session(work)
