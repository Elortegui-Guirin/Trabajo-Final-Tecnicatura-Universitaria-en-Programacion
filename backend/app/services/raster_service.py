# Servicio de análisis raster - Núcleo de procesamiento GeoTIFF
import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_geom
from rasterio.crs import CRS
from shapely.geometry import shape, mapping
from shapely.ops import transform as shapely_transform
from pyproj import Transformer
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from app.models.lot import Lot
from app.models.analysis import Analysis
from app.core.raster_config import get_raster_path, get_raster_source, ResourceType

logger = logging.getLogger(__name__)


async def clip_raster_to_geometry(
    raster_path: str,
    geometry: dict,
    target_crs: Optional[str] = None,
) -> tuple[np.ndarray, rasterio.Affine, dict]:
    """
    Recorta un raster GeoTIFF a una geometría (polígono).
    
    Returns:
        - data: array numpy 2D (band, height, width) -> squeeze a 2D
        - transform: affine transform del recorte
        - meta: metadata del raster original
    """
    with rasterio.open(raster_path) as src:
        # Leer metadata
        meta = src.meta.copy()
        src_crs = src.crs
        
        # Transformar geometría al CRS del raster si es necesario
        geom = geometry
        if src_crs and target_crs and str(src_crs) != target_crs:
            geom = transform_geom("EPSG:4326", src_crs, geometry)
        elif src_crs:
            geom = transform_geom("EPSG:4326", src_crs, geometry)
        
        # Recortar (mask)
        out_image, out_transform = mask(
            src,
            [geom],
            crop=True,
            nodata=src.nodata,
            filled=True,
        )
        
        # out_image shape: (bands, height, width) -> tomar primera banda
        data = out_image[0] if out_image.ndim == 3 else out_image
        
        return data, out_transform, meta


def calculate_statistics(
    data: np.ndarray,
    nodata: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calcula estadísticas descriptivas de un array raster recortado.
    Ignora valores nodata y NaN.
    """
    # Filtrar valores válidos
    valid_mask = np.ones_like(data, dtype=bool)
    if nodata is not None:
        valid_mask &= (data != nodata)
    valid_mask &= ~np.isnan(data)
    
    valid_data = data[valid_mask]
    
    if valid_data.size == 0:
        return {
            "mean": None,
            "min": None,
            "max": None,
            "std": None,
            "percentiles": {},
            "count": 0,
        }
    
    stats = {
        "mean": float(np.mean(valid_data)),
        "min": float(np.min(valid_data)),
        "max": float(np.max(valid_data)),
        "std": float(np.std(valid_data)),
        "percentiles": {
            "p25": float(np.percentile(valid_data, 25)),
            "p50": float(np.percentile(valid_data, 50)),
            "p75": float(np.percentile(valid_data, 75)),
            "p90": float(np.percentile(valid_data, 90)),
            "p95": float(np.percentile(valid_data, 95)),
        },
        "count": int(valid_data.size),
    }
    
    return stats


async def analyze_lot_resource(
    session: AsyncSession,
    lot_id: UUID,
    resource_type: ResourceType,
    base_raster_path: str = "/data/rasters",
) -> Analysis:
    """
    Ejecuta análisis completo: recorta raster al lote, calcula estadísticas, guarda en BD.
    """
    # 1. Obtener lote con geometría
    stmt = select(Lot).where(Lot.id == lot_id)
    result = await session.exec(stmt)
    lot = result.first()
    
    if not lot:
        raise ValueError(f"Lote {lot_id} no encontrado")
    
    # 2. Obtener path del raster
    raster_path = get_raster_path(resource_type, base_raster_path)
    raster_source = get_raster_source(resource_type)
    
    # 3. Convertir geometría WKB a GeoJSON dict
    from geoalchemy2.shape import to_shape
    lot_geom = to_shape(lot.geometry)
    geom_geojson = mapping(lot_geom)
    
    # 4. Recortar raster
    logger.info(f"Recortando raster {raster_path} para lote {lot_id}")
    data, out_transform, meta = clip_raster_to_geometry(
        raster_path=raster_path,
        geometry=geom_geojson,
    )
    
    # 5. Calcular estadísticas
    nodata = raster_source.nodata
    stats = calculate_statistics(data, nodata=nodata)
    
    if stats["count"] == 0:
        raise ValueError("No hay datos válidos en el recorte (lote fuera de bounds del raster)")
    
    # 6. Crear registro de análisis
    analysis = Analysis(
        lot_id=lot_id,
        resource_type=resource_type.value,
        average_rate=stats["mean"],
        min_value=stats["min"],
        max_value=stats["max"],
        std_dev=stats["std"],
        percentiles=stats["percentiles"],
        raster_file_reference=raster_path,
        analyzed_at=datetime.utcnow(),
        status="completed",
        error_message=None,
    )
    
    session.add(analysis)
    await session.commit()
    await session.refresh(analysis)
    
    logger.info(f"Análisis completado: {analysis.id}, tasa={stats['mean']:.4f}")
    return analysis


async def run_analysis_task(
    session: AsyncSession,
    analysis_id: UUID,
    base_raster_path: str = "/data/rasters",
) -> Analysis:
    """
    Task en background: actualiza status a processing, ejecuta análisis, actualiza resultado.
    """
    # Obtener análisis pendiente
    stmt = select(Analysis).where(Analysis.id == analysis_id)
    result = await session.exec(stmt)
    analysis = result.first()
    
    if not analysis:
        raise ValueError(f"Análisis {analysis_id} no encontrado")
    
    # Marcar como processing
    analysis.status = "processing"
    await session.commit()
    
    try:
        # Ejecutar análisis
        resource_type = ResourceType(analysis.resource_type)
        completed = await analyze_lot_resource(
            session=session,
            lot_id=analysis.lot_id,
            resource_type=resource_type,
            base_raster_path=base_raster_path,
        )
        return completed
    except Exception as e:
        # Marcar como failed
        analysis.status = "failed"
        analysis.error_message = str(e)
        await session.commit()
        logger.error(f"Análisis {analysis_id} falló: {e}")
        raise


async def get_time_series(
    session: AsyncSession,
    lot_id: UUID,
    resource_type: ResourceType,
) -> list:
    """Obtiene serie temporal de análisis para un lote y recurso."""
    stmt = (
        select(Analysis)
        .where(
            Analysis.lot_id == lot_id,
            Analysis.resource_type == resource_type.value,
            Analysis.status == "completed",
        )
        .order_by(Analysis.analyzed_at)
    )
    result = await session.exec(stmt)
    analyses = result.all()
    
    return [
        {
            "analyzed_at": a.analyzed_at,
            "average_rate": a.average_rate,
            "resource_type": a.resource_type,
        }
        for a in analyses
    ]