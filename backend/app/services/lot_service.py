# Servicio de lotes - Lógica de negocio
from typing import List, Optional, Tuple
from uuid import UUID
from shapely.geometry import shape, Polygon, mapping
from shapely.ops import transform
from pyproj import Transformer
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from geoalchemy2.functions import ST_GeomFromGeoJSON, ST_Area, ST_Transform, ST_SetSRID

from app.models.lot import Lot
from app.models.user import User


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
    # Centroide para determinar zona UTM
    centroid = polygon.centroid
    lon, lat = centroid.x, centroid.y
    
    # Calcular zona UTM (WGS84)
    utm_zone = int((lon + 180) / 6) + 1
    if lat >= 0:
        epsg = 32600 + utm_zone  # Norte
    else:
        epsg = 32700 + utm_zone  # Sur
    
    # Transformar a UTM y calcular área en m²
    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
    polygon_utm = transform(transformer.transform, polygon)
    
    area_m2 = polygon_utm.area
    return round(area_m2 / 10000, 4)  # m² a hectáreas


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
    return lot


async def get_lots(
    session: AsyncSession,
    user_id: UUID,
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None
) -> Tuple[List[Lot], int]:
    """Obtiene lotes paginados del usuario."""
    stmt = select(Lot).where(Lot.user_id == user_id)
    
    if search:
        stmt = stmt.where(Lot.name.ilike(f"%{search}%"))
    
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
    user_id: UUID
) -> Optional[Lot]:
    """Obtiene un lote verificando ownership."""
    stmt = select(Lot).where(Lot.id == lot_id, Lot.user_id == user_id)
    result = await session.exec(stmt)
    return result.first()


async def update_lot(
    session: AsyncSession,
    lot_id: UUID,
    user_id: UUID,
    name: Optional[str] = None,
    geometry: Optional[dict] = None
) -> Optional[Lot]:
    """Actualiza lote verificando ownership."""
    lot = await get_lot(session, lot_id, user_id)
    if not lot:
        return None
    
    if name is not None:
        lot.name = name
    
    if geometry is not None:
        polygon = await validate_geometry(geometry)
        lot.area_ha = await calculate_area_ha(polygon)
        lot.geometry = ST_SetSRID(ST_GeomFromGeoJSON(str(geometry).replace("'", '"')), 4326)
    
    await session.commit()
    await session.refresh(lot)
    return lot


async def delete_lot(
    session: AsyncSession,
    lot_id: UUID,
    user_id: UUID
) -> bool:
    """Elimina lote verificando ownership."""
    lot = await get_lot(session, lot_id, user_id)
    if not lot:
        return False
    
    await session.delete(lot)
    await session.commit()
    return True


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
    }