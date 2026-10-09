# Servicio de geometría - Validación y procesamiento server-side
from typing import List, Optional, Tuple
from shapely.geometry import shape, Polygon, MultiPolygon, mapping
from shapely.ops import transform, unary_union, polygonize
from shapely.validation import make_valid
from shapely.geometry.polygon import orient
from shapely.simplify import simplify as shapely_simplify
from pyproj import Transformer
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape, from_shape
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.schemas.geometry import (
    GeoJSONPolygon, 
    GeometryValidationResult, 
    GeometryValidationConfig,
    MAX_VERTICES,
    MIN_AREA_HA,
    MAX_AREA_HA,
)


def _count_vertices(polygon: Polygon) -> int:
    """Cuenta vértices del anillo exterior (excluyendo punto de cierre)."""
    return len(polygon.exterior.coords) - 1


def _simplify_polygon(polygon: Polygon, tolerance: float = 0.00001) -> Tuple[Polygon, bool]:
    """
    Simplifica un polígono usando Douglas-Peucker.
    Returns: (simplified_polygon, was_simplified)
    """
    vertex_count = _count_vertices(polygon)
    if vertex_count <= MAX_VERTICES:
        return polygon, False
    
    simplified = shapely_simplify(polygon, tolerance, preserve_topology=True)
    
    # Verificar que la simplificación no rompió la geometría
    if simplified.is_valid and simplified.geom_type == "Polygon" and not simplified.is_empty:
        new_count = _count_vertices(simplified)
        if new_count <= MAX_VERTICES:
            return simplified, True
        # Si sigue teniendo muchos vértices, aumentar tolerancia
        return _simplify_polygon(simplified, tolerance * 2)
    
    return polygon, False


def _validate_geometry_shapely(
    geom_dict: dict, 
    config: GeometryValidationConfig
) -> Tuple[Optional[Polygon], List[str], List[str]]:
    """
    Valida geometría usando Shapely.
    Returns: (polygon, errors, warnings)
    """
    errors: List[str] = []
    warnings: List[str] = []
    
    try:
        geom = shape(geom_dict)
    except Exception as e:
        return None, [f"Error parseando GeoJSON: {str(e)}], warnings
    
    # 1. Verificar multipolígono
    if geom.geom_type == "MultiPolygon":
        if config.reject_multipolygon:
            return None, [f"Multipolígonos no permitidos. Recibido {geom.geom_type} con {len(geom.geoms)} polígonos. Por favor, dibuje un solo polígono."], warnings
        else:
            # Unir todos los polígonos
            warnings.append(f"Multipolígono detectado ({len(geom.geoms)} partes). Unificando en un solo polígono.")
            geom = unary_union(list(geom.geoms))
            if geom.geom_type == "Polygon":
                geom = geom
            elif geom.geom_type == "MultiPolygon":
                # Tomar el de mayor área como fallback
                geom = max(geom.geoms, key=lambda p: p.area)
                warnings.append("Multipolígono con partes no contiguas: se tomó el de mayor área.")
            else:
                return None, [f"Resultado de unión inválido: {geom.geom_type}"], warnings
    
    elif geom.geom_type != "Polygon":
        return None, [f"Geometría debe ser Polygon, recibido {geom.geom_type}"], warnings
    
    # 2. Validar geometría básica
    if not geom.is_valid:
        errors.append("Geometría inválida (self-intersection, anillos mal formados)")
    
    if geom.is_empty:
        errors.append("Geometría vacía")
    
    # 3. Asegurar orientación correcta (exterior CCW, interiores CW)
    try:
        geom = orient(geom, sign=1.0)
    except Exception as e:
        errors.append(f"Error orientando geometría: {str(e)}")
    
    # 4. Corregir con make_valid si hay errores
    if not geom.is_valid:
        try:
            fixed = make_valid(geom)
            if fixed.is_valid and fixed.geom_type == "Polygon":
                geom = fixed
                warnings.append("Geometría corregida automáticamente con make_valid")
            else:
                errors.append("No se pudo corregir la geometría automáticamente")
        except Exception:
            errors.append("Error al intentar corregir geometría")
    
    if errors:
        return None, errors, warnings
    
    # 5. Límite de vértices + simplificación automática
    vertex_count = _count_vertices(geom)
    if vertex_count > config.max_vertices:
        simplified, was_simplified = _simplify_polygon(geom, config.simplify_tolerance)
        if was_simplified:
            geom = simplified
            warnings.append(f"Geometría simplificada de {vertex_count} a {_count_vertices(geom)} vértices (tolerancia {config.simplify_tolerance}°)")
        else:
            return None, [f"Demasiados vértices: {vertex_count}. Máximo permitido: {config.max_vertices}. Simplifique el polígono."], warnings
    
    return geom, [], warnings


def _calculate_area_ha(polygon: Polygon) -> Optional[float]:
    """Calcula área en hectáreas proyectando a UTM óptima."""
    try:
        centroid = polygon.centroid
        lon, lat = centroid.x, centroid.y
        utm_zone = int((lon + 180) / 6) + 1
        if lat >= 0:
            epsg = 32600 + utm_zone
        else:
            epsg = 32700 + utm_zone
        transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
        polygon_utm = transform(transformer.transform, polygon)
        area_m2 = polygon_utm.area
        return round(area_m2 / 10000, 4)
    except Exception:
        return None


def validate_and_fix_geometry(
    geojson: dict,
    config: Optional[GeometryValidationConfig] = None
) -> GeometryValidationResult:
    """
    Validación server-side de geometría GeoJSON.
    
    Steps:
    1. shape(geojson) → Shapely geometry
    2. Rechazar Multipolygon (configurable)
    3. make_valid() para corregir self-intersections menores
    4. Verifica geom_type == 'Polygon', is_valid, not is_empty
    5. Límite de vértices (MAX_VERTICES) con simplificación Douglas-Peucker
    6. Validar área mínima (MIN_AREA_HA) y máxima (MAX_AREA_HA)
    7. Proyecta a UTM óptima → area_ha
    8. Retorna GeoJSON validado (WGS84) + área + flags + warnings
    """
    if config is None:
        config = GeometryValidationConfig()
    
    result = GeometryValidationResult(valid=True)
    
    polygon, errors, warnings = _validate_geometry_shapely(geojson, config)
    
    if errors:
        result.valid = False
        result.errors = errors
        result.warnings = warnings
        result.fixed_geometry = None
        result.area_ha = None
        return result
    
    # Validar área
    if polygon is not None:
        area_ha = _calculate_area_ha(polygon)
        result.area_ha = area_ha
        
        if area_ha is not None:
            if area_ha < config.min_area_ha:
                result.valid = False
                result.errors.append(
                    f"Área demasiado pequeña: {area_ha:.4f} ha. "
                    f"Mínimo: {config.min_area_ha} ha ({config.min_area_ha * 10000:.0f} m²)"
                )
            elif area_ha > config.max_area_ha:
                result.valid = False
                result.errors.append(
                    f"Área demasiado grande: {area_ha:.4f} ha. "
                    f"Máximo: {config.max_area_ha} ha ({config.max_area_ha / 100:.0f} km²)"
                )
        
        # Crear GeoJSON del polígono validado
        try:
            fixed_geom_dict = mapping(polygon)
            result.fixed_geometry = GeoJSONPolygon(**fixed_geom_dict)
        except Exception:
            pass
    
    result.warnings = warnings
    
    # Si hay errores de área, invalidar
    if result.errors:
        result.valid = False
        result.fixed_geometry = None
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
        return wkt.dumps(geom)
    except Exception:
        return "GEOMETRY EMPTY"