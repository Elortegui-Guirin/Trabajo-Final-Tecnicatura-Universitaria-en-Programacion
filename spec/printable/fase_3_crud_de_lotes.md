# Fase 3 – CRUD de Lotes

## 🎯 Objetivo de la Fase
Implementar CRUD completo de lotes/parcelas georreferenciadas: creación con geometría GeoJSON, listado paginado con filtros avanzados, obtención de detalle, actualización (nombre, geometría, recálculo área), y **soft delete**. Validación estricta de geometrías (Polígono válido, SRID 4326, sin self-intersections), **área mínima**, **versionado de geometrías** y **filtros espaciales/avanzados**.

## 📦 Artefactos Generados en esta Fase
- `backend/app/schemas/lot.py` – Pydantic: `LotCreate`, `LotUpdate`, `LotRead`, `LotListResponse`, `GeometryInput`, `LotVersionRead`, `LotSearchParams`, constantes `MIN_AREA_HA`/`MAX_AREA_HA`
- `backend/app/routers/lots.py` – Endpoints: `POST /lots`, `GET /lots`, `GET /lots/{id}`, `PATCH /lots/{id}`, `DELETE /lots/{id}`, `POST /lots/{id}/restore`, `GET /lots/{id}/versions`
- `backend/app/services/lot_service.py` – Lógica: `create_lot()`, `get_lots()`, `get_lot()`, `update_lot()`, `delete_lot()`, `restore_lot()`, `get_lot_versions()`, `validate_geometry()`, `calculate_area_ha()`, `validate_area()`, `create_lot_version()`
- `backend/app/models/lot.py` – Modelo SQLModel: UUID, FK user, name, area_ha, geometry(Geometry), **deleted_at**, timestamps
- `backend/app/models/lot_version.py` – Modelo SQLModel: **Historial de geometrías** (lot_id, version_number, name, area_ha, geometry, changed_by, change_reason, created_at)
- `backend/app/api/deps.py` – Dependencia `get_current_active_user` (filtro ownership + soft-delete + lockout)
- `backend/tests/test_lots.py` – Tests: CRUD, validación geometría/área, ownership, paginación, filtros avanzados, versionado, soft delete/restore
- `backend/alembic/versions/005_lot_versions.py` – Migración tabla `lot_versions` + índices + unique constraint
- `frontend/src/modules/lots/` – Módulo completo:
  - `components/LotForm.tsx` – Formulario crear/editar con **motivo de cambio**, validación área mínima
  - `components/LotList.tsx` – Tabla paginada con **filtros avanzados** (fecha, rango área, bbox, estado)
  - `components/LotDetail.tsx` – Vista detalle: mapa solo lectura + métricas + **historial de versiones** + estado eliminado/restaurar
  - `hooks/useLots.ts` – Queries/mutations: `useLots()`, `useLot()`, `useLotVersions()`, `useCreateLot()`, `useUpdateLot()`, `useDeleteLot()`, `useRestoreLot()`
  - `api/lotsApi.ts` – Cliente tipado con nuevos endpoints
  - `pages/LotsPage.tsx`, `LotDetailPage.tsx`, `LotFormPage.tsx`
- `frontend/src/components/MapView/MapEditor.tsx` – Componente reutilizable mapa + draw/edit

## 🧩 Detalle Técnico

### Backend (FastAPI + SQLModel)
**Endpoints creados:**
| Método | Ruta | Body/Params | Response | Descripción |
|--------|------|-------------|----------|-------------|
| POST | `/lots` | `LotCreate{name, geometry: GeoJSON}` | `LotRead` (201) | Crea lote, valida geometría/área mínima, calcula área_ha, crea versión v1 |
| GET | `/lots` | `?page=1&size=20&search=&date_from=&date_to=&area_min=&area_max=&bbox=&include_deleted=` | `LotListResponse` | Listado paginado con **filtros avanzados**: búsqueda, rango fechas, rango área, bbox espacial, incluir eliminados |
| GET | `/lots/{id}` | — | `LotRead` | Detalle lote (verifica ownership, filtra soft-delete) |
| PATCH | `/lots/{id}` | `LotUpdate{name?, geometry?, change_reason?}` | `LotRead` | Actualiza campos; si geometry → revalida + recalcula área + **crea versión histórica** |
| DELETE | `/lots/{id}` | — | 204 | **Soft delete**: marca `deleted_at`, **conserva analyses** para auditoría |
| POST | `/lots/{id}/restore` | — | `LotRead` | Restaura lote soft-deleted |
| GET | `/lots/{id}/versions` | — | `List[LotVersionRead]` | Historial de geometrías ordenado descendente (vN...v1) |

**Esquemas Pydantic (nuevos/actualizados):**
```python
# Constantes de validación
MIN_AREA_HA = 0.01  # 100 m² mínimo
MAX_AREA_HA = 10000  # 10,000 ha máximo

class LotCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    geometry: GeometryInput

class LotUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    geometry: Optional[dict] = None
    change_reason: Optional[str] = Field(default=None, max_length=500)

class LotRead(BaseModel):
    id: UUID
    name: str
    area_ha: float
    geometry: dict  # GeoJSON
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

class LotVersionRead(BaseModel):
    id: UUID
    lot_id: UUID
    version_number: int
    name: str
    area_ha: float
    geometry: dict  # GeoJSON
    changed_by: UUID
    change_reason: Optional[str] = None
    created_at: datetime

class LotSearchParams(BaseModel):
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    area_min: Optional[float] = Field(default=None, ge=MIN_AREA_HA)
    area_max: Optional[float] = Field(default=None, le=MAX_AREA_HA)
    bbox: Optional[List[float]] = Field(default=None, min_length=4, max_length=4)  # [min_lon, min_lat, max_lon, max_lat]
    include_deleted: bool = False
```

**Servicio `lot_service.py` (nuevas funciones):**
- `validate_area(area_ha: float)`: Valida límites `MIN_AREA_HA` (0.01 ha = 100 m²) y `MAX_AREA_HA` (10,000 ha)
- `get_next_version_number()`: Obtiene próximo número de versión incremental por lote
- `create_lot_version()`: Crea registro en `lot_versions` con geometría, área, nombre, usuario, motivo
- `create_lot()`: Valida área → crea lote → crea versión v1 ("Creación inicial")
- `update_lot()`: Si cambia geometría → valida área → **crea versión histórica** antes de actualizar
- `get_lots()`: Filtros avanzados: `search`, `date_from/to`, `area_min/max`, `bbox` (ST_Intersects), `include_deleted`
- `get_lot_versions()`: Historial ordenado descendente (vN...v1)
- `restore_lot()`: Restaura soft-delete (`deleted_at = NULL`)

### Frontend (React + TypeScript)
**Componentes React actualizados:**
- `LotForm`: Campo **motivo del cambio** (solo edición), validación Zod + `change_reason`
- `LotList`: **Filtros avanzados colapsables** (fecha desde/hasta, área min/max, bbox), badges estado (Activo/Eliminado), botón **Restaurar** para eliminados
- `LotDetail`: Badge **Eliminado**, métricas incluyen fecha eliminación, **historial de versiones colapsable** (tabla vN...v1 con área, motivo, fecha, usuario), botón **Restaurar** si eliminado
- `useLots.ts`: Keys versionadas, hooks `useLotVersions()`, `useRestoreLot()`, params `LotSearchParams`

### Base de Datos (PostgreSQL/PostGIS)
- **Migración 005** (`alembic/versions/005_lot_versions.py`):
  - Tabla `lot_versions`: id, lot_id(FK), version_number, name, area_ha, geometry(POLYGON,4326), changed_by(FK users), change_reason, created_at
  - Índices: `lot_id`, `(lot_id, version_number)` unique, `changed_by`, `created_at`
  - FK `lot_id` CASCADE, FK `changed_by` CASCADE
- **Migración 003** (Fase 1): Columna `deleted_at` en `lots` + índice, `lot_versions` FK hacia `lots` con ON DELETE CASCADE
- Trigger `updated_at` funcional

## ✅ Criterios de Aceptación de la Fase
- [ ] `POST /lots` con GeoJSON Polygon válido + área ≥ 0.01 ha → 201, lote creado, `area_ha` correcto, **versión v1 creada**
- [ ] `POST /lots` con área < 0.01 ha → 422 "Área demasiado pequeña: mínimo 0.01 ha"
- [ ] `POST /lots` con geometría inválida → 422 error descriptivo
- [ ] `GET /lots` con filtros: `search`, `date_from/to`, `area_min/max`, `bbox` → resultados filtrados correctamente
- [ ] `PATCH /lots/{id}` con geometría → recalcula `area_ha` + **crea versión histórica** (vN) con motivo
- [ ] `PATCH /lots/{id}` solo nombre → **NO crea versión**
- [ ] `DELETE /lots/{id}` → 204, soft delete (`deleted_at` set), **NO elimina analyses** (auditoría)
- [ ] `POST /lots/{id}/restore` → 200, lote restaurado (`deleted_at = NULL`)
- [ ] `GET /lots/{id}/versions` → lista descendente (vN...v1) con área, motivo, usuario, fecha
- [ ] `GET /lots` con `bbox` → filtro espacial `ST_Intersects` funciona
- [ ] Frontend: crear/editar lote muestra **validación área mínima** (0.01 ha), campo **motivo de cambio**
- [ ] Frontend: listado con **filtros avanzados** (fecha, área, bbox), badges **Activo/Eliminado**, botón **Restaurar**
- [ ] Frontend: detalle muestra **historial versiones** (vN...v1), badge **Eliminado**, botón **Restaurar**
- [ ] Tests backend: `pytest backend/tests/test_lots.py -v` → todos pasan (incl. área mínima, versionado, soft delete, filtros)
- [ ] `make lint` / `npm run lint` pasan

## 🔗 Dependencias con otras Fases
- **Requisito previo**: Fase 1 (modelo Lot, DB, migraciones, deleted_at), Fase 2 (auth, `get_current_user`, ownership, lockout)
- **Habilita**: Fase 4 (mapa interactivo usa `LotMapEditor` y endpoints lotes), Fase 5 (análisis requiere lote existente + geometría válida + versionado para comparación temporal)