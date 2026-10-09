# Servicio de lotes - Lógica de negocio
from typing import List, Optional, Tuple
from uuid import UUID
from shapely.geometry import shape, Polygon, mapping, box
from shapely.ops import transform
from pyproj import Transformer
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func, and_, or_
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from geoalchemy2.functions import ST_GeomFromGeoJSON, ST_SetSRID, ST_Intersects, ST_MakeEnvelope
from datetime import datetime, timezone

from app.models.lot import Lot
from app.models.lot_version import LotVersion
from app.models.user import User

# Constantes
MIN_AREA_HA = 0.01  # 100 m²
MAX_AREA_HA = 10000  # 10,000 ha


async def validate_geometry(geom_dict: dict) -> Polygon:
    """Valida y normaliza geometría GeoJSON a Shapely Polygon en WGS84."""
    geom = shape(geom_dict)
    
    if geom.geom_type != "Polygon":
        raise ValueError(f"Geometría debe ser Polygon, recibido {geom.geom_type}")
    
    if not geom.is_valid:
        raise ValueError("Geometría inválida (self-intersection, anillos mal formados)")
    
    if geom.is_empty:
        raise ValueError("Geometría vacía")
    
    # Asegurar orientación correcta (exterior CCW, interiores CW)
    from shapely.geometry.polygon import orient
    geom = orient(geom, sign=1.0)
    
    return geom


async def calculate_area_ha(polygon: Polygon) -> float:
    """Calcula área en hectáreas proyectando a UTM zona adecuada."""
    centroid = polygon.centroid
    lon, lat = centroid.x, centroid.y
    
    utm_zone = int((lon + 180) / 6) + 1
    if lat >= 0:
        epsg = 32600 + utm_zone  # Norte
    else:
        epsg = 32700 + utm_zone  # Sur
    
    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
    polygon_utm = transform(transformer.transform, polygon)
    
    area_m2 = polygon_utm.area
    return round(area_m2 / 10000, 4)  # m² a hectáreas


async def validate_area(area_ha: float) -> None:
    """Valida que el área esté dentro de límites razonables."""
    if area_ha < MIN_AREA_HA:
        raise ValueError(f"Área demasiado pequeña: {area_ha:.4f} ha. Mínimo: {MIN_AREA_HA} ha (100 m²)")
    if area_ha > MAX_AREA_HA:
        raise ValueError(f"Área demasiado grande: {area_ha:.4f} ha. Máximo: {MAX_AREA_HA} ha")


async def get_next_version_number(session: AsyncSession, lot_id: UUID) -> int:
    """Obtiene el próximo número de versión para un lote."""
    from sqlmodel import select, func
    stmt = select(func.max(LotVersion.version_number)).where(LotVersion.lot_id == lot_id)
    result = await session.exec(stmt)
    max_version = result.first()
    return (max_version or 0) + 1


async def create_lot_version(
    session: AsyncSession,
    lot: Lot,
    changed_by: UUID,
    change_reason: Optional[str] = None
) -> LotVersion:
    """Crea una nueva versión histórica del lote."""
    version_number = await get_next_version_number(session, lot.id)
    
    version = LotVersion(
        lot_id=lot.id,
        version_number=version_number,
        name=lot.name,
        area_ha=lot.area_ha,
        geometry=lot.geometry,
        changed_by=changed_by,
        change_reason=change_reason,
    )
    session.add(version)
    await session.flush()
    return version


async def create_lot(
    session: AsyncSession,
    user_id: UUID,
    name: str,
    geometry: dict
) -> Lot:
    """Crea un nuevo lote con geometría validada y área calculada."""
    # Validar geometría
    polygon = await validate_geometry(geometry)
    area_ha = await calculate_area_ha(polygon)
    
    # Validar área
    await validate_area(area_ha)
    
    # Convertir a WKB para PostGIS
    geom_wkb = ST_SetSRID(ST_GeomFromGeoJSON(str(geometry).replace("'", '"')), 4326)
    
    lot = Lot(
        user_id=user_id,
        name=name,
        area_ha=area_ha,
        geometry=geom_wkb,
    )
    session.add(lot)
    await session.commit()
    await session.refresh(lot)
    
    # Crear versión inicial (v1)
    await create_lot_version(session, lot, user_id, "Creación inicial")
    await session.commit()
    await session.refresh(lot)
    
    return lot


async def get_lots(
    session: AsyncSession,
    user_id: UUID,
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    area_min: Optional[float] = None,
    area_max: Optional[float] = None,
    bbox: Optional[List[float]] = None,
    include_deleted: bool = False
) -> Tuple[List[Lot], int]:
    """Obtiene lotes paginados del usuario con filtros avanzados."""
    stmt = select(Lot).where(Lot.user_id == user_id)
    
    # Filtro soft-delete
    if not include_deleted:
        stmt = stmt.where(Lot.deleted_at.is_(None))
    
    # Búsqueda por nombre
    if search:
        stmt = stmt.where(Lot.name.ilike(f"%{search}%"))
    
    # Filtro por fecha de creación
    if date_from:
        stmt = stmt.where(Lot.created_at >= date_from)
    if date_to:
        stmt = stmt.where(Lot.created_at <= date_to)
    
    # Filtro por rango de área
    if area_min is not None:
        stmt = stmt.where(Lot.area_ha >= area_min)
    if area_max is not None:
        stmt = stmt.where(Lot.area_ha <= area_max)
    
    # Filtro por bounding box (intersección espacial)
    if bbox and len(bbox) == 4:
        min_lon, min_lat, max_lon, max_lat = bbox
        # Crear envelope bbox en PostGIS
        bbox_geom = ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        stmt = stmt.where(ST_Intersects(Lot.geometry, bbox_geom))
    
    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.exec(count_stmt)).first()
    
    # Paginación
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Lot.created_at.desc())
    lots = (await session.exec(stmt)).all()
    
    return list(lots), total


async def get_lot(
    session: AsyncSession,
    lot_id: UUID,
    user_id: UUID,
    include_deleted: bool = False
) -> Optional[Lot]:
    """Obtiene un lote verificando ownership."""
    stmt = select(Lot).where(Lot.id == lot_id, Lot.user_id == user_id)
    if not include_deleted:
        stmt = stmt.where(Lot.deleted_at.is_(None))
    result = await session.exec(stmt)
    return result.first()


async def update_lot(
    session: AsyncSession,
    lot_id: UUID,
    user_id: UUID,
    name: Optional[str] = None,
    geometry: Optional[dict] = None,
    change_reason: Optional[str] = None
) -> Optional[Lot]:
    """Actualiza lote verificando ownership y crea versión histórica si cambia geometría."""
    lot = await get_lot(session, lot_id, user_id)
    if not lot:
        return None
    
    geometry_changed = False
    
    if name is not None:
        lot.name = name
    
    if geometry is not None:
        polygon = await validate_geometry(geometry)
        area_ha = await calculate_area_ha(polygon)
        await validate_area(area_ha)
        
        lot.area_ha = area_ha
        lot.geometry = ST_SetSRID(ST_GeomFromGeoJSON(str(geometry).replace("'", '"')), 4326)
        geometry_changed = True
    
    # Si cambió la geometría, crear versión histórica ANTES de commitear
    if geometry_changed:
        await create_lot_version(session, lot, user_id, change_reason or "Modificación de geometría")
    
    await session.commit()
    await session.refresh(lot)
    return lot


async def delete_lot(
    session: AsyncSession,
    lot_id: UUID,
    user_id: UUID
) -> bool:
    """Soft delete: marca lote como eliminado (deleted_at). Los analyses se conservan."""
    lot = await get_lot(session, lot_id, user_id)
    if not lot:
        return False
    
    lot.deleted_at = datetime.now(timezone.utc)
    await session.commit()
    return True


async def restore_lot(
    session: AsyncSession,
    lot_id: UUID,
    user_id: UUID
) -> bool:
    """Restaura un lote soft-deleted."""
    from sqlmodel import select
    stmt = select(Lot).where(Lot.id == lot_id, Lot.user_id == user_id)
    result = await session.exec(stmt)
    lot = result.first()
    if not lot or lot.deleted_at is None:
        return False
    
    lot.deleted_at = None
    await session.commit()
    return True


async def get_lot_versions(
    session: AsyncSession,
    lot_id: UUID,
    user_id: UUID
) -> List[LotVersion]:
    """Obtiene el historial de versiones de un lote."""
    # Verificar ownership
    lot = await get_lot(session, lot_id, user_id, include_deleted=True)
    if not lot:
        return []
    
    from sqlmodel import select
    stmt = (
        select(LotVersion)
        .where(LotVersion.lot_id == lot_id)
        .order_by(LotVersion.version_number.desc())
    )
    result = await session.exec(stmt)
    return list(result.all())


async def lot_to_read(lot: Lot) -> dict:
    """Convierte modelo Lot a dict para respuesta (con GeoJSON)."""
    from geoalchemy2.shape import to_shape
    geom = to_shape(lot.geometry)
    return {
        "id": lot.id,
        "name": lot.name,
        "area_ha": float(lot.area_ha),
        "geometry": mapping(geom),
        "created_at": lot.created_at,
        "updated_at": lot.updated_at,
        "deleted_at": lot.deleted_at,
    }