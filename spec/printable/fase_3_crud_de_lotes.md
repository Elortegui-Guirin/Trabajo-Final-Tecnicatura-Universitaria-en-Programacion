# Fase 3 – CRUD de Lotes

## 🎯 Objetivo de la Fase
Implementar CRUD completo de lotes/parcelas georreferenciadas: creación con geometría GeoJSON, listado paginado con filtros, obtención de detalle, actualización (nombre, geometría, recálculo área), y eliminación en cascada. Validación estricta de geometrías (Polígono válido, SRID 4326, sin self-intersections).

## 📦 Artefactos Generados en esta Fase
- `backend/app/schemas/lot.py` – Pydantic: `LotCreate`, `LotUpdate`, `LotRead`, `LotListResponse`, `GeometryInput`
- `backend/app/routers/lots.py` – Endpoints: `POST /lots`, `GET /lots`, `GET /lots/{id}`, `PATCH /lots/{id}`, `DELETE /lots/{id}`
- `backend/app/services/lot_service.py` – Lógica: `create_lot()`, `get_lots()`, `get_lot()`, `update_lot()`, `delete_lot()`, `validate_geometry()`, `calculate_area_ha()`
- `backend/app/models/lot.py` – Modelo SQLModel completo con híbridos, propiedades, validadores
- `backend/app/api/deps.py` – Dependencia `get_current_user_lots` (filtro por ownership)
- `backend/tests/test_lots.py` – Tests: CRUD completo, validación geometría, ownership, paginación, área
- `frontend/src/modules/lots/` – Módulo completo:
  - `components/LotForm.tsx` – Formulario crear/editar (nombre + mapa embebido para geometría)
  - `components/LotList.tsx` – Tabla paginada con TanStack Table: columnas nombre, área, acciones
  - `components/LotDetail.tsx` – Vista detalle: mapa solo lectura + métricas + botón análisis
  - `components/LotMapEditor.tsx` – Componente mapa Leaflet + draw/edit (reutiliza Fase 4)
  - `hooks/useLots.ts` – Queries/mutations TanStack Query: `useLots()`, `useLot()`, `useCreateLot()`, `useUpdateLot()`, `useDeleteLot()`
  - `api/lotsApi.ts` – Cliente API tipado
  - `pages/LotsPage.tsx` – Listado + botón nuevo
  - `pages/LotDetailPage.tsx` – Detalle por ID
  - `pages/LotFormPage.tsx` – Crear/editar (rutas `/lots/new`, `/lots/:id/edit`)
- `frontend/src/components/MapView/MapEditor.tsx` – Componente reutilizable mapa + draw (base para Fase 4)

## 🧩 Detalle Técnico

### Backend (FastAPI + SQLModel)
**Endpoints creados:**
| Método | Ruta | Body/Params | Response | Descripción |
|--------|------|-------------|----------|-------------|
| POST | `/lots` | `LotCreate{name, geometry: GeoJSON}` | `LotRead` (201) | Crea lote, valida geometría, calcula área_ha, asigna user_id del token |
| GET | `/lots` | `?page=1&size=20&search=` | `LotListResponse{items: LotRead[], total, page, size}` | Listado paginado del usuario autenticado |
| GET | `/lots/{id}` | — | `LotRead` | Detalle lote (verifica ownership) |
| PATCH | `/lots/{id}` | `LotUpdate{name?, geometry?}` | `LotRead` | Actualiza campos; si geometry → revalida + recalcula área |
| DELETE | `/lots/{id}` | — | 204 | Elimina lote + analyses en cascada (FK ON DELETE CASCADE) |

**Esquemas Pydantic:**
```python
class GeometryInput(BaseModel):
    type: Literal["Polygon"]
    coordinates: list[list[list[float]]]  # [[[lon, lat], ...]] anillo exterior + interiores

class LotCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    geometry: GeometryInput

class LotUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    geometry: GeometryInput | None = None

class LotRead(BaseModel):
    id: UUID
    name: str
    area_ha: float
    geometry: dict  # GeoJSON dict
    created_at: datetime
    updated_at: datetime
```

**Servicio `lot_service.py`:**
- `validate_geometry(geom: dict) -> Polygon`: Shapely `shape()` → valida `is_valid`, `geom_type == 'Polygon'`, transforma a SRID 4326 si necesario, rechaza self-intersections
- `calculate_area_ha(polygon: Polygon) -> float`: Proyección a UTM zona adecuada (via `pyproj`) → área m² → hectáreas
- `create_lot()`: `geometry` → WKB `ST_GeomFromGeoJSON` → INSERT; `area_ha` calculado server-side (no confiar en cliente)

### Frontend (React + TypeScript)
**Componentes React:**
- `LotForm`: RHF + Zod (esquema `LotCreate`/`LotUpdate`), integra `MapEditor` para dibujo polígono, muestra área calculada en tiempo real
- `LotList`: TanStack Table v8 con paginación server-side, ordenación, búsqueda por nombre; acciones: ver, editar, eliminar (confirm modal)
- `LotDetail`: Mapa solo lectura (`MapView` readonly) + cards: nombre, área, fecha creación, botón "Analizar" (link a Fase 5)
- `MapEditor`: Leaflet + `leaflet.pm` toolbar (draw polygon, edit, delete layer), `onDrawEnd` emite GeoJSON válido

**Estado/Queries (TanStack Query):**
```typescript
// Query keys
const lotKeys = {
  all: ['lots'] as const,
  lists: () => [...lotKeys.all, 'list'] as const,
  list: (params: ListParams) => [...lotKeys.lists(), params] as const,
  detail: (id: string) => [...lotKeys.all, 'detail', id] as const,
};

// Mutations con invalidación
useCreateLot: () => mutation({ onSuccess: () => queryClient.invalidateQueries({ queryKey: lotKeys.lists() }) })
useUpdateLot: () => mutation({ onSuccess: (_, vars) => queryClient.invalidateQueries({ queryKey: lotKeys.detail(vars.id) }) })
useDeleteLot: () => mutation({ onSuccess: () => queryClient.invalidateQueries({ queryKey: lotKeys.lists() }) })
```

### Base de Datos (PostgreSQL/PostGIS)
- **Migración 003** (si no incluida en 001): Asegurar `geometry` con `SRID 4326`, `CHECK (ST_GeometryType(geometry) = 'ST_Polygon')`, `CHECK (ST_IsValid(geometry))`
- Índice GIST ya creado en Fase 1 (`idx_lots_geometry`)
- Trigger `updated_at` funcional

## ✅ Criterios de Aceptación de la Fase
- [ ] `POST /lots` con GeoJSON Polygon válido → 201, lote creado, `area_ha` calculado correctamente (verificar con `ST_Area(geography)/10000`)
- [ ] `POST /lots` con geometría inválida (no polígono, self-intersection, SRID erróneo) → 422 error descriptivo
- [ ] `GET /lots` paginado retorna solo lotes del usuario autenticado (ownership)
- [ ] `PATCH /lots/{id}` actualiza nombre; si envía geometry → recalcula `area_ha`
- [ ] `DELETE /lots/{id}` elimina lote y sus analyses (CASCADE verificado en BD)
- [ ] Frontend: crear lote dibuja polígono en mapa → envía → aparece en listado con área correcta
- [ ] Frontend: editar lote permite modificar geometría (draw/edit) → recalcula área
- [ ] Frontend: listado paginado, búsqueda, ordenación funcionan sin recarga completa
- [ ] Tests backend: `pytest backend/tests/test_lots.py -v` → todos pasan (incl. edge cases geometría)
- [ ] `make lint` / `npm run lint` pasan

## 🔗 Dependencias con otras Fases
- **Requisito previo**: Fase 1 (modelo Lot, DB, migraciones), Fase 2 (auth, `get_current_user`, ownership)
- **Habilita**: Fase 4 (mapa interactivo usa `LotMapEditor` y endpoints lotes), Fase 5 (análisis requiere lote existente + geometría)