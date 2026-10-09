# Tareas periódicas para Celery Beat
from celery import shared_task
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def update_all_raster_layers() -> dict:
    """
    Task programada: actualizar todas las capas raster desde fuente origen.
    Ejecutar diariamente via Celery Beat (2:00 AM).
    """
    logger.info("Iniciando actualización programada de capas raster...")
    
    # TODO: Implementar lógica real de actualización
    # 1. Conectar a Google Earth Engine / Sentinel Hub / NASA
    # 2. Descargar nuevas imágenes
    # 3. Procesar y generar GeoTIFF actualizados
    # 4. Reemplazar archivos en /data/rasters/
    # 5. Actualizar versiones en RASTER_CATALOG (raster_config.py)
    # 6. Opcional: re-analizar lotes afectados
    
    logger.info("Actualización de capas raster completada")
    return {"status": "completed", "message": "Actualización de capas raster completada", "timestamp": datetime.now(timezone.utc).isoformat()}


@shared_task
def generate_alerts_for_anomalies() -> dict:
    """
    Detectar anomalías en análisis recientes y generar alertas.
    Ejecutar diariamente via Celery Beat (3:00 AM).
    """
    import asyncio
    from datetime import timedelta
    
    async def _check():
        from sqlmodel.ext.asyncio.session import AsyncSession
        from sqlmodel import select, and_
        from app.db.database import async_session_maker
        from app.models.analysis import Analysis, AnalysisStatus
        from app.models.lot import Lot
        from app.models.user import User
        from app.services import notification_service
        
        async with async_session_maker() as session:
            # Buscar análisis recientes completados (últimas 24h)
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
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
                # Obtener histórico del mismo lote+recurso
                stmt = (
                    select(Analysis)
                    .where(
                        Analysis.lot_id == analysis.lot_id,
                        Analysis.resource_type == analysis.resource_type,
                        Analysis.status == AnalysisStatus.COMPLETED,
                        Analysis.id != analysis.id,
                    )
                    .order_by(Analysis.analyzed_at.desc())
                    .limit(10)
                )
                historical = (await session.exec(stmt)).all()
                
                if len(historical) >= 3:
                    avg_historical = sum(h.average_rate for h in historical) / len(historical)
                    if analysis.average_rate < avg_historical * 0.1:  # < 10% del promedio
                        # Crear alerta
                        lot = await session.get(Lot, analysis.lot_id)
                        if lot:
                            user = await session.get(User, lot.user_id)
                            if user:
                                alerts.append({
                                    "type": "low_growth_alert",
                                    "user_id": user.id,
                                    "lot_id": analysis.lot_id,
                                    "analysis_id": analysis.id,
                                    "message": f"Crecimiento anómalo detectado en lote {lot.name}: {analysis.average_rate:.2f} vs promedio histórico {avg_historical:.2f}",
                                })
            
            # Enviar notificaciones (email, push, etc.)
            for alert in alerts:
                await notification_service.send_alert(alert)
            
            return {"alerts_generated": len(alerts), "analyzed": len(alerts)}
    
    return asyncio.run(_check())


@shared_task
def cleanup_old_reports(days: int = 30) -> dict:
    """
    Limpia reportes PDF antiguos.
    Ejecutar semanalmente.
    """
    import os
    from pathlib import Path
    
    report_dir = Path("/data/reports")
    if not report_dir.exists():
        return {"deleted": 0, "message": "Directorio de reportes no existe"}
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    deleted = 0
    
    for report_file in report_dir.glob("*.pdf"):
        try:
            mtime = datetime.fromtimestamp(report_file.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                report_file.unlink()
                deleted += 1
        except Exception as e:
            logger.warning(f"Error eliminando {report_file}: {e}")
    
    return {"deleted": deleted, "cutoff_date": cutoff.isoformat()}


@shared_task
def cleanup_stale_analyses(hours: int = 2) -> dict:
    """
    Limpia análisis que quedaron en PROCESSING por más de N horas.
    Ejecutar cada hora.
    """
    import asyncio
    
    async def _cleanup():
        from sqlmodel.ext.asyncio.session import AsyncSession
        from sqlmodel import select, and_
        from app.db.database import async_session_maker
        from app.models.analysis import Analysis, AnalysisStatus
        
        async with async_session_maker() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            stmt = select(Analysis).where(
                and_(
                    Analysis.status == AnalysisStatus.PROCESSING,
                    Analysis.updated_at < cutoff,
                )
            )
            result = await session.exec(stmt)
            stale = result.all()
            
            count = 0
            for analysis in stale:
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = f"Análisis abandonado (timeout > {hours}h en PROCESSING)"
                count += 1
            
            await session.commit()
            return {"marked_failed": count, "cutoff": cutoff.isoformat()}
    
    return asyncio.run(_cleanup())