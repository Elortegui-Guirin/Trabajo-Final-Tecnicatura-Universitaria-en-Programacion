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
from sqlmodel import select, and_
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
import logging

from app.models.lot import Lot
from app.models.analysis import Analysis, ResourceType, AnalysisStatus
from app.core.raster_config import get_raster_path, get_raster_source, get_raster_version, get_raster_date
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _compute_geometry_hash(geometry: dict) -> str:
    """Calcula SHA256 de la geometría para cache."""
    import json
    import hashlib
    geom_str = json.dumps(geometry, sort_keys=True)
    return hashlib.sha256(geom_str.encode()).hexdigest()


def clip_raster_to_geometry(
    raster_path: str,
    geometry: dict,
    target_crs: Optional[str] = None,
    all_touched: bool = False,
) -> Tuple[np.ndarray, rasterio.Affine, dict]:
    """
    Recorta un raster GeoTIFF a una geometría (polígono).
    
    Returns:
        - data: array numpy 2D (band, height, width) -> squeeze a 2D
        - transform: affine transform del recorte
        - meta: metadata del raster original
    """
    with rasterio.open(raster_path) as src:
        meta = src.meta.copy()
        src_crs = src.crs
        
        geom = geometry
        if src_crs and target_crs and str(src_crs) != target_crs:
            geom = transform_geom("EPSG:4326", src_crs, geometry)
        elif src_crs:
            geom = transform_geom("EPSG:4326", src_crs, geometry)
        
        # filled=False -> array enmascarado: quedan marcados como inválidos los píxeles
        # fuera del polígono y los NoData del archivo (si no, se rellenaban con 0
        # cuando el .tif no tiene NoData y bajaban el promedio).
        out_image, out_transform = mask(
            src,
            [geom],
            crop=True,
            filled=False,
            # False: solo píxeles cuyo centro cae dentro del lote.
            # True: todo píxel que toque el lote (para lotes más chicos que un píxel).
            all_touched=all_touched,
        )
        
        data = out_image[0] if out_image.ndim == 3 else out_image
        
        return data, out_transform, meta


def calculate_statistics(
    data: np.ndarray,
    nodata: Optional[float] = None,
    valid_min: Optional[float] = None,
    valid_max: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calcula estadísticas descriptivas de un array raster recortado.
    Ignora valores nodata y NaN.
    """
    valid_mask = np.ones(np.shape(data), dtype=bool)
    if np.ma.isMaskedArray(data):
        valid_mask &= ~np.ma.getmaskarray(data)
        data = np.ma.getdata(data)
    if nodata is not None:
        valid_mask &= (data != nodata)
    valid_mask &= ~np.isnan(data)
    if valid_min is not None:
        valid_mask &= (data >= valid_min)
    if valid_max is not None:
        valid_mask &= (data <= valid_max)
    
    valid_data = data[valid_mask]
    
    if valid_data.size == 0:
        return {
            "mean": None, "min": None, "max": None, "std": None,
            "percentiles": {}, "count": 0,
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


async def _check_concurrent_analysis(
    session: AsyncSession,
    lot_id: UUID,
    resource_type: ResourceType,
    exclude_id: Optional[UUID] = None,
) -> Optional[Analysis]:
    """Verifica si ya hay un análisis en curso (pending/processing) para este lote y recurso."""
    stmt = select(Analysis).where(
        and_(
            Analysis.lot_id == lot_id,
            Analysis.resource_type == resource_type,
            Analysis.status.in_([AnalysisStatus.PENDING, AnalysisStatus.PROCESSING])
        )
    )
    if exclude_id is not None:
        stmt = stmt.where(Analysis.id != exclude_id)
    result = await session.exec(stmt)
    return result.first()


async def _check_cache(
    session: AsyncSession, 
    lot_id: UUID, 
    resource_type: ResourceType, 
    geometry_hash: str, 
    raster_version: str
) -> Optional[Analysis]:
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
    
    result = await session.exec(stmt)
    return result.first()


async def analyze_lot_resource(
    session: AsyncSession,
    lot_id: UUID,
    resource_type: ResourceType,
    base_raster_path: str = "/data/rasters",
    store_clipped: bool = False,
    analysis: Optional[Analysis] = None,
) -> Analysis:
    """
    Ejecuta análisis completo: recorta raster al lote, calcula estadísticas, guarda en BD.
    Incluye cache y versionado de raster.

    Si se pasa `analysis` (el registro pending creado por el endpoint), se actualiza
    ESE registro con los resultados en lugar de crear uno nuevo.
    """
    # 1. Obtener lote con geometría
    stmt = select(Lot).where(Lot.id == lot_id)
    result = await session.exec(stmt)
    lot = result.first()
    
    if not lot:
        raise ValueError(f"Lote {lot_id} no encontrado")
    
    # 2. Obtener configuración del raster
    raster_path = get_raster_path(resource_type, base_raster_path)
    raster_source = get_raster_source(resource_type)
    raster_version = get_raster_version(resource_type)
    raster_date = get_raster_date(resource_type)
    
    # 3. Convertir geometría WKB a GeoJSON dict
    from geoalchemy2.shape import to_shape
    lot_geom = to_shape(lot.geometry)
    geom_geojson = mapping(lot_geom)
    
    # 4. Calcular hash de geometría para cache
    geometry_hash = _compute_geometry_hash(geom_geojson)
    
    # 5. Verificar cache: ¿ya existe análisis idéntico? (solo si no hay registro a completar;
    #    el endpoint POST /analyses ya verificó el cache antes de crear el pending)
    cached = None
    if analysis is None:
        cached = await _check_cache(session, lot_id, resource_type, geometry_hash, raster_version)
    if cached:
        logger.info(f"Cache hit para lote {lot_id} + recurso {resource_type.value} + versión {raster_version}")
        return cached
    
    # 6. Recortar raster
    logger.info(f"Recortando raster {raster_path} para lote {lot_id}")
    data, out_transform, meta = clip_raster_to_geometry(
        raster_path=raster_path,
        geometry=geom_geojson,
    )
    
    # 7. Calcular estadísticas
    # NoData: el del catálogo si está definido, si no el del archivo
    nodata = raster_source.nodata if raster_source.nodata is not None else meta.get("nodata")
    stats = calculate_statistics(
        data, nodata=nodata,
        valid_min=raster_source.valid_min, valid_max=raster_source.valid_max,
    )

    # Lote más chico que un píxel (MODIS ~11 ha): ningún centro de píxel cae adentro.
    # Se repite tomando todos los píxeles que el lote toca.
    if stats["count"] == 0:
        logger.info(f"Lote {lot_id}: sin centros de píxel dentro, reintento con all_touched=True")
        data, out_transform, meta = clip_raster_to_geometry(
            raster_path=raster_path,
            geometry=geom_geojson,
            all_touched=True,
        )
        stats = calculate_statistics(
            data, nodata=nodata,
            valid_min=raster_source.valid_min, valid_max=raster_source.valid_max,
        )

    if stats["count"] == 0:
        raise ValueError(
            "No hay datos válidos en el lote: está fuera de la zona cubierta por el mapa "
            "o sobre áreas sin dato (zonas urbanas, agua)."
        )
    
    # 8. Opcional: guardar raster recortado
    clipped_raster_path = None
    if store_clipped:
        import os
        clipped_dir = f"{base_raster_path}/clipped"
        os.makedirs(clipped_dir, exist_ok=True)
        clipped_filename = f"clipped_{uuid4().hex}.tif"
        clipped_raster_path = f"{clipped_dir}/{clipped_filename}"
        
        # Rellenar lo enmascarado (fuera del lote / NoData) con un valor NoData válido
        fill_value = nodata
        if fill_value is None:
            fill_value = -9999 if np.issubdtype(data.dtype, np.floating) else 0
        clipped = np.ma.filled(data, fill_value)

        with rasterio.open(
            clipped_raster_path, 'w',
            driver='GTiff',
            height=clipped.shape[0],
            width=clipped.shape[1],
            count=1,
            dtype=clipped.dtype,
            crs=meta['crs'],
            transform=out_transform,
            nodata=fill_value,
        ) as dst:
            dst.write(clipped, 1)
        
        logger.info(f"Raster recortado guardado en {clipped_raster_path}")
    
    # 9. Guardar resultados (en el registro existente o en uno nuevo)
    results = dict(
        average_rate=stats["mean"],
        min_value=stats["min"],
        max_value=stats["max"],
        std_dev=stats["std"],
        percentiles=stats["percentiles"],
        raster_file_reference=raster_path,
        raster_version=raster_version,
        raster_date=raster_date,
        clipped_raster_path=clipped_raster_path,
        store_clipped_raster=store_clipped,
        lot_geometry_hash=geometry_hash,
        analyzed_at=datetime.now(timezone.utc),
        status=AnalysisStatus.COMPLETED,
        error_message=None,
    )
    if analysis is None:
        analysis = Analysis(lot_id=lot_id, resource_type=resource_type, **results)
    else:
        for field, value in results.items():
            setattr(analysis, field, value)
    
    session.add(analysis)
    await session.commit()
    await session.refresh(analysis)
    
    logger.info(f"Análisis completado: {analysis.id}, tasa={stats['mean']:.4f}, cache={cached is not None}")
    return analysis


async def run_analysis_task(
    session: AsyncSession,
    analysis_id: UUID,
    base_raster_path: str = "/data/rasters",
) -> Analysis:
    """
    Task en background: actualiza status a processing, ejecuta análisis, actualiza resultado.
    Incluye control de concurrencia y cache.
    """
    # Obtener análisis pendiente
    stmt = select(Analysis).where(Analysis.id == analysis_id)
    result = await session.exec(stmt)
    analysis = result.first()
    
    if not analysis:
        raise ValueError(f"Análisis {analysis_id} no encontrado")
    
    # === CONTROL DE CONCURRENCIA ===
    existing = await _check_concurrent_analysis(
        session, analysis.lot_id, ResourceType(analysis.resource_type), exclude_id=analysis.id
    )
    if existing and existing.status == AnalysisStatus.PROCESSING:
        raise ValueError(
            f"Ya existe un análisis en curso para este lote y recurso "
            f"(ID: {existing.id}, estado: {existing.status}). "
            f"Reintente en 30 segundos."
        )
    
    # Marcar como processing
    analysis.status = AnalysisStatus.PROCESSING
    await session.commit()
    
    try:
        # Ejecutar análisis
        resource_type = ResourceType(analysis.resource_type)
        completed = await analyze_lot_resource(
            session=session,
            lot_id=analysis.lot_id,
            resource_type=resource_type,
            base_raster_path=base_raster_path,
            store_clipped=analysis.store_clipped_raster,
            analysis=analysis,
        )
        return completed
    except Exception as e:
        # Marcar como failed (rollback por si la sesión quedó en estado inválido)
        await session.rollback()
        analysis.status = AnalysisStatus.FAILED
        analysis.error_message = str(e)[:1000]
        session.add(analysis)
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
            Analysis.resource_type == ResourceType(resource_type),
            Analysis.status == AnalysisStatus.COMPLETED,
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
            "raster_version": a.raster_version,
            "raster_date": a.raster_date.isoformat() if a.raster_date else None,
        }
        for a in analyses
    ]


async def check_analysis_cache(
    session: AsyncSession,
    lot_id: UUID,
    resource_type: ResourceType,
    geometry_hash: str,
    raster_version: str,
) -> Optional[Analysis]:
    """
    Verifica si existe un análisis en cache para los parámetros dados.
    Retorna el análisis si existe, None en caso contrario.
    """
    return await _check_cache(session, lot_id, resource_type, geometry_hash, raster_version)