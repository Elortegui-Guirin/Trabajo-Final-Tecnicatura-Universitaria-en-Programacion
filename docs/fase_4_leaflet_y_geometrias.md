# Fase 4 – Integración de Leaflet y Geometrías

## 🎯 Objetivo de la Fase
Integrar mapa interactivo completo con Leaflet en el frontend: visualización de capas base (OSM, Satélite), dibujo y edición de polígonos con `leaflet.pm`, captura de GeoJSON válido (SRID 4326), sincronización con formularios de lotes, y renderizado de lotes existentes como capas vectoriales con popups informativos. **Incluye validación robusta: rechazo de multipolígonos, límite de vértices (5000) con simplificación automática, validación de área mínima, panel de validación visual.**

## 📦 Artefactos Generados en esta Fase
- `frontend/src/components/MapView/` – Componentes de mapa reutilizables:
  - `MapContainer.tsx` – Wrapper Leaflet `Map` + capas base + controles
  - `BaseLayers.tsx` – Capas: OpenStreetMap, CartoDB Voyager, Esri World Imagery (satelital)
  - `DrawControl.tsx` – Toolbar `leaflet.pm` (polígono, editar, eliminar, cortar) + contador vértices
  - `VectorLayer.tsx` – Capa GeoJSON con estilos condicionales + popups
  - `MapEditor.tsx` – Componente alto nivel: mapa + draw + callbacks `onGeometryChange(geojson)` + **panel de validación visual**
  - `MapView.tsx` – Componente solo lectura para detalle/listado (sin toolbar)
  - `useMap.ts` – Hook encapsula lógica Leaflet: `mapRef`, `addLayer()`, `removeLayer()`, `fitBounds()`
- `frontend/src/modules/lots/components/LotMapEditor.tsx` – Integración en formulario lotes (ya creado Fase 3, aquí se completa)
- `frontend/src/modules/map/pages/MapPage.tsx` – Página mapa global (opcional, vista general todos los lotes)
- `frontend/src/hooks/useGeoJSON.ts` – Utilidades: `validatePolygon(geojson)`, `calculateAreaHa(geojson)`, `simplifyGeometry(geojson, tolerance)`, `getVertexCount(geojson)`, constantes `MAX_VERTICES=5000`, `MIN_AREA_HA=0.01`
- `frontend/src/styles/map.css` – Estilos Leaflet personalizados + **panel de validación visual** (errores, warnings, vértices, área)
- `backend/app/schemas/geometry.py` – Esquemas compartidos: `GeoJSONPolygon`, `GeometryValidationResult`, `GeometryValidationConfig`, constantes `MAX_VERTICES=5000`, `MIN_AREA_HA=0.01`, `MAX_AREA_HA=10000`
- `backend/app/services/geometry_service.py` – Validación server-side reutilizable: `validate_and_fix_geometry()` con **rechazo de multipolígonos**, **límite de vértices (5000) con simplificación Douglas-Peucker automática**, **validación de área (0.01-10000 ha)**, warnings de simplificación

## 🧩 Detalle Técnico

### Backend (FastAPI + SQLModel)
**Esquemas compartidos (`schemas/geometry.py`):**
```python
class GeoJSONPolygon(BaseModel):
    type: Literal["Polygon"]
    coordinates: List[List[List[float]]]  # [exterior_ring, interior_ring*]

class GeometryValidationResult(BaseModel):
    valid: bool
    errors: List[str] = []
    fixed_geometry: Optional[GeoJSONPolygon] = None
    area_ha: Optional[float] = None
    warnings: List[str] = []

# Constantes
MAX_VERTICES = 5000
MIN_AREA_HA = 0.01  # 100 m²
MAX_AREA_HA = 10000  # 10,000 ha

class GeometryValidationConfig(BaseModel):
    max_vertices: int = MAX_VERTICES
    min_area_ha: float = MIN_AREA_HA
    max_area_ha: float = MAX_AREA_HA
    simplify_tolerance: float = 0.00001  # ~1m en WGS84
    reject_multipolygon: bool = True
```

**Servicio `geometry_service.py` (mejoras):**
- `validate_and_fix_geometry(geojson: dict, config: GeometryValidationConfig) -> GeometryValidationResult`:
  1. `shape(geojson)` → Shapely geometry
  2. **Rechazar Multipolygon** (configurable) con mensaje claro
  3. `make_valid()` (GEOS 3.8+) para corregir self-intersections menores
  4. Verifica `geom_type == 'Polygon'`, `is_valid`, `not is_empty`
  5. **Límite de vértices (5000)** con simplificación Douglas-Peucker automática (`tolerance=0.00001°` ~1m)
  6. **Validar área** (MIN_AREA_HA=0.01 ha, MAX_AREA_HA=10000 ha)
  7. Proyecta a UTM óptima → `area_ha`
  8. Retorna GeoJSON validado (WGS84) + área + flags + **warnings de simplificación**
- `to_geojson(db_geometry: WKBElement) -> dict`: `ST_AsGeoJSON` via session
- `from_geojson(geojson: dict) -> WKBElement`: `ST_GeomFromGeoJSON` para INSERT/UPDATE

### Frontend (React + TypeScript)
**Componentes MapView actualizados:**
- `MapEditor`: **Panel de validación visual** (errores rojos, warnings amarillos, vértices con badge, área con validación mínima) + botón limpiar
- `DrawControl`: Contador de vértices en tiempo real, warning en consola al acercarse a 4000/5000
- `useGeoJSON.ts`: `validatePolygon()` retorna `{valid, errors, warnings, vertexCount, areaHa}`, `simplifyGeometry()` con Douglas-Peucker, `getVertexCount()`, `calculateAreaHa()`
- `map.css`: Panel de validación visual (errores rojos, warnings amarillos, badges de vértices/área, badges de error/warning)

**Integración en `LotForm`:**
- `MapEditor` muestra validación en tiempo real (errores, warnings, vértices, área)
- Cálculo área cliente-side vía `useGeoJSON.calculateAreaHa()` para feedback inmediato (server valida definitivo)
- Simplificación automática antes de enviar a backend

### Base de Datos (PostgreSQL/PostGIS)
- Validación server-side en `lot_service.py` usa `geometry_service.validate_and_fix_geometry()`
- Función PL/pgSQL opcional para validación en BD:
  ```sql
  CREATE OR REPLACE FUNCTION validate_lot_geometry(geom geometry)
  RETURNS boolean AS $$
  BEGIN
      RETURN ST_IsValid(geom) AND ST_GeometryType(geom) = 'ST_Polygon'
           AND ST_NPoints(geom) <= 5001
           AND ST_Area(geog) >= 100;  -- 100 m² = 0.01 ha
  END; $$ LANGUAGE plpgsql;
  ```

## ✅ Criterios de Aceptación de la Fase
- [ ] Mapa carga capas base (OSM, Satélite) sin errores de consola, controles de capa funcionan
- [ ] Toolbar `leaflet.pm` permite: dibujar polígono, editar vértices, eliminar polígono, cortar polígono
- [ ] **Multipolígonos rechazados** con mensaje claro: "Multipolígonos no permitidos..."
- [ ] **Límite de vértices**: 5000 máx. Simplificación automática Douglas-Peucker si excede. Warning en consola >4000 vértices
- [ ] **Área mínima**: 0.01 ha (100 m²) validada en frontend y backend
- [ ] Al dibujar/editar, `onGeometryChange` emite GeoJSON **Polygon** válido (anillo exterior CCW, interiores CW)
- [ ] GeoJSON emitido tiene coordenadas `[lon, lat]` (WGS84 / EPSG:4326)
- [ ] **Panel de validación visual**: errores rojos, warnings amarillos, badge vértices (rojo >5000, amarillo >4000), badge área (rojo <0.01 ha), warnings de simplificación
- [ ] `MapEditor` en formulario lotes: crea nuevo → geometría capturada → POST `/lots` exitoso
- [ ] `MapEditor` en edición: carga geometría existente → permite modificar → PATCH `/lots/{id}` recalcula área
- [ ] `MapView` (solo lectura) renderiza lote con popup: nombre, área (ha), fecha creación
- [ ] Validación server-side rechaza geometrías inválidas con mensaje claro (ej: "Multipolígonos no permitidos", "Área demasiado pequeña: 0.005 ha. Mínimo: 0.01 ha")
- [ ] `make lint` / `npm run lint` pasan; build producción (`npm run build`) sin errores

## 🔗 Dependencias con otras Fases
- **Requisito previo**: Fase 1 (estructura frontend, Tailwind), Fase 3 (endpoints lotes, esquemas, `LotMapEditor` base)
- **Habilita**: Fase 5 (análisis raster necesita geometría válida del lote para recorte GeoTIFF)