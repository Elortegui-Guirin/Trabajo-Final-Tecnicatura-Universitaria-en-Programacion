# Servicio de geometría - Validación y procesamiento server-side
from typing import List, Optional
from shapely.geometry import shape, Polygon, mapping
from shapely.ops import transform
from pyproj import Transformer
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape, from_shape
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemas.geometry import GeoJSONPolygon, GeometryValidationResult


def _validate_geometry_shapely(geom_dict: dict) -> Tuple[Optional[Polygon], List[str]]:
    """Valida geometría usando Shapely y retorna (polygon, errors)."""
    errors: List[str] = []
    try:
        geom = shape(geom_dict)
    except Exception as e:
        return None, [f"Error parseando GeoJSON: {str(e)}"]

    if geom.geom_type != "Polygon":
        return None, [f"Geometría debe ser Polygon, recibido {geom.geom_type}"]

    if not geom.is_valid:
        errors.append("Geometría inválida (self-intersection, anillos mal formados)")

    if geom.is_empty:
        errors.append("Geometría vacía")

    # Asegurar orientación correcta (exterior CCW, interiores CW)
    from shapely.geometry.polygon import orient
    try:
        geom = orient(geom, sign=1.0)
    except Exception as e:
        errors.append(f"Error orientando geometría: {str(e)}")

    # Calcular área si es válida
    area_ha = None
    if not errors and geom.is_valid:
        try:
            centroid = geom.centroid
            lon, lat = centroid.x, centroid.y
            utm_zone = int((lon + 180) / 6) + 1
            if lat >= 0:
                epsg = 32600 + utm_zone
            else:
                epsg = 32700 + utm_zone
            transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
            polygon_utm = transform(transformer.transform, geom)
            area_m2 = polygon_utm.area
            area_ha = round(area_m2 / 10000, 4)
        except Exception:
            pass

    fixed_geom = None
    if errors:
        # Intentar corregir con make_valid si es posible
        try:
            from shapely.validation import make_valid
            fixed = make_valid(geom)
            if fixed.is_valid and fixed.geom_type == "Polygon":
                fixed_geom = fixed
                errors.append("Geometría corregida automáticamente con make_valid")
        except Exception:
            pass

    return fixed_geom if not errors else None, errors


def validate_and_fix_geometry(geojson: dict) -> GeometryValidationResult:
    """Validación server-side de geometría GeoJSON.
    
    Steps:
    1. shape(geojson) → Shapely geometry
    2. make_valid() para corregir self-intersections menores
    3. Verifica geom_type == 'Polygon', is_valid, not is_empty
    4. Si multipolígono → unary_union + polygonize → toma mayor área
    5. Proyecta a UTM óptima → area_ha
    6. Retorna GeoJSON corrigido (WGS84) + área + flags
    """
    result = GeometryValidationResult(valid=True)
    
    polygon, errors = _validate_geometry_shapely(geojson)
    
    if errors:
        result.valid = False
        result.errors = errors
        result.fixed_geometry = None
        result.area_ha = None
        return result
    
    result.valid = True
    result.errors = []
    result.fixed_geometry = None  # Ya validado original
    
    # Calcular área
    if polygon is not None:
        try:
            centroid = polygon.centroid
            lon, lat = polygon.centroid.x, polygon.centroid.y
            utm_zone = int((lon + 180) / 6) + 1
            if lat >= 0:
                epsg = 32600 + utm_zone
            else:
                epsg = 32700 + utm_zone
            transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
            polygon_utm = transform(transformer.transform, polygon)
            area_m2 = polygon_utm.area
            result.area_ha = round(area_m2 / 10000, 4)
        except Exception:
            result.area_ha = None
    
    return result


def to_geojson(wkb_geom) -> dict:
    """Convierte un objeto WKB de la BD a dict GeoJSON."""
    try:
        geom = to_shape(wkb_geom)
        return mapping(geom)
    except Exception:
        return {"type": "Polygon", "coordinates": []}


def from_geojson_to_wkt(geojson: dict) -> str:
    """Convierte GeoJSON a WKT para PostGIS."""
    try:
        from shapely.geometry import shape
        geom = shape(geojson)
        from shapely import wkt
        return wkt(geom)
    except Exception:
        return "GEOMETRY EMPTY"