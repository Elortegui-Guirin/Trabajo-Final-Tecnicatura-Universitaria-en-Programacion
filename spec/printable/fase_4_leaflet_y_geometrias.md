# Fase 4 – Integración de Leaflet y Geometrías

## 🎯 Objetivo de la Fase
Integrar mapa interactivo completo con Leaflet en el frontend: visualización de capas base (OSM, Satélite), dibujo y edición de polígonos con `leaflet.pm`, captura de GeoJSON válido (SRID 4326), sincronización con formularios de lotes, y renderizado de lotes existentes como capas vectoriales con popups informativos.

## 📦 Artefactos Generados en esta Fase
- `frontend/src/components/MapView/` – Componentes de mapa reutilizables:
  - `MapContainer.tsx` – Wrapper Leaflet `Map` + capas base + controles
  - `BaseLayers.tsx` – Capas: OpenStreetMap, CartoDB Voyager, Esri World Imagery (satelital)
  - `DrawControl.tsx` – Toolbar `leaflet.pm` (polígono, editar, eliminar, cortar)
  - `VectorLayer.tsx` – Capa GeoJSON con estilos condicionales + popups
  - `MapEditor.tsx` – Componente alto nivel: mapa + draw + callbacks `onGeometryChange(geojson)`
  - `MapView.tsx` – Componente solo lectura para detalle/listado (sin toolbar)
  - `useMap.ts` – Hook encapsula lógica Leaflet: `mapRef`, `addLayer()`, `removeLayer()`, `fitBounds()`
- `frontend/src/modules/lots/components/LotMapEditor.tsx` – Integración en formulario lotes (ya creado Fase 3, aquí se completa)
- `frontend/src/modules/map/pages/MapPage.tsx` – Página mapa global (opcional, vista general todos los lotes)
- `frontend/src/hooks/useGeoJSON.ts` – Utilidades: `validatePolygon(geojson)`, `calculateAreaHa(geojson)`, `simplifyGeometry(geojson, tolerance)`
- `frontend/src/styles/map.css` – Estilos Leaflet personalizados (override .leaflet-container, .pm-toolbar)
- `backend/app/schemas/geometry.py` – Esquemas compartidos: `GeoJSONPolygon`, `GeometryValidationResult`
- `backend/app/services/geometry_service.py` – Validación server-side reutilizable: `validate_and_fix_geometry()`, `to_geojson()`, `from_geojson()`

## 🧩 Detalle Técnico

### Backend (FastAPI + SQLModel)
**Esquemas compartidos (`schemas/geometry.py`):**
```python
class GeoJSONPolygon(BaseModel):
    type: Literal["Polygon"]
    coordinates: list[list[list[float]]]  # [exterior_ring, interior_ring*]

class GeometryValidationResult(BaseModel):
    valid: bool
    errors: list[str] = []
    fixed_geometry: GeoJSONPolygon | None = None
    area_ha: float | None = None
```

**Servicio `geometry_service.py`:**
- `validate_and_fix_geometry(geojson: dict) -> GeometryValidationResult`:
  1. `shape(geojson)` → Shapely geometry
  2. `make_valid()` (GEOS 3.8+) para corregir self-intersections menores
  3. Verifica `geom_type == 'Polygon'`, `is_valid`, `not is_empty`
  4. Si multipolígono → `unary_union` + `polygonize` → toma mayor área
  5. Proyecta a UTM óptima → `area_ha`
  6. Retorna GeoJSON corrigido (WGS84) + área + flags
- `to_geojson(db_geometry: WKBElement) -> dict`: `ST_AsGeoJSON` via session
- `from_geojson(geojson: dict) -> WKBElement`: `ST_GeomFromGeoJSON` para INSERT/UPDATE

### Frontend (React + TypeScript)
**Componentes MapView:**
- `MapContainer`: Inicializa `Map` (center default [-34.6, -58.4], zoom 10), `LayersControl` para capas base, `AttributionControl`
- `BaseLayers`: `TileLayer` URLs parametrizadas, subdomains, maxZoom 19
- `DrawControl`: `pm.addControls({ position: 'topleft', drawMarker: false, drawPolyline: false, drawRectangle: false, drawCircle: false, drawPolygon: true, editMode: true, removalMode: true, cutPolygon: true })`
  - Eventos: `pm:create` → `onDrawEnd(geojson)`, `pm:edit` → `onEditEnd(geojson)`, `pm:remove` → `onRemove()`
- `VectorLayer`: `GeoJSON` component con `style()` function (color por propiedad), `onEachFeature` para `bindPopup` con nombre + área
- `MapEditor`: Orquesta `MapContainer` + `DrawControl` + `VectorLayer` (capa temporal dibujo), expone `geometry` state + `setGeometry(geojson)`

**Hook `useMap`:**
```typescript
interface UseMapReturn {
  mapRef: React.RefObject<L.Map | null>;
  addGeoJSON: (geojson: GeoJSON.FeatureCollection, layerId: string, style?: L.PathOptions) => void;
  removeLayer: (layerId: string) => void;
  fitToLayer: (layerId: string, padding?: number) => void;
  getMap: () => L.Map | null;
}
```

**Integración en `LotForm`:**
- `MapEditor` en modo "edit" recibe `initialGeometry` (existente) o `null` (nuevo)
- `onGeometryChange` actualiza campo oculto `geometry` del formulario (RHF `watch`/`setValue`)
- Cálculo área cliente-side vía `useGeoJSON.calculateAreaHa()` para feedback inmediato (server valida definitivo)

### Base de Datos (PostgreSQL/PostGIS)
- Sin migraciones nuevas (esquema definido Fase 1)
- Validación server-side en `lot_service.py` usa `geometry_service.validate_and_fix_geometry()`
- Función PL/pgSQL opcional para validación en BD:
  ```sql
  CREATE OR REPLACE FUNCTION validate_lot_geometry(geom geometry)
  RETURNS boolean AS $$
  BEGIN
      RETURN ST_IsValid(geom) AND ST_GeometryType(geom) = 'ST_Polygon';
  END; $$ LANGUAGE plpgsql;
  ```

## ✅ Criterios de Aceptación de la Fase
- [ ] Mapa carga capas base (OSM, Satélite) sin errores de consola, controles de capa funcionan
- [ ] Toolbar `leaflet.pm` permite: dibujar polígono, editar vértices, eliminar polígono, cortar polígono
- [ ] Al dibujar/editar, `onGeometryChange` emite GeoJSON **Polygon** válido (anillo exterior CCW, interiores CW)
- [ ] GeoJSON emitido tiene coordenadas `[lon, lat]` (WGS84 / EPSG:4326)
- [ ] `MapEditor` en formulario lotes: crea nuevo → geometría capturada → POST `/lots` exitoso
- [ ] `MapEditor` en edición: carga geometría existente → permite modificar → PATCH `/lots/{id}` recalcula área
- [ ] `MapView` (solo lectura) renderiza lote con popup: nombre, área (ha), fecha creación
- [ ] Validación server-side rechaza geometrías inválidas con mensaje claro (ej: "Self-intersection en anillo 0")
- [ ] `make lint` / `npm run lint` pasan; build producción (`npm run build`) sin errores

## 🔗 Dependencias con otras Fases
- **Requisito previo**: Fase 1 (estructura frontend, Tailwind), Fase 3 (endpoints lotes, esquemas, `LotMapEditor` base)
- **Habilita**: Fase 5 (análisis raster necesita geometría válida del lote para recorte GeoTIFF)