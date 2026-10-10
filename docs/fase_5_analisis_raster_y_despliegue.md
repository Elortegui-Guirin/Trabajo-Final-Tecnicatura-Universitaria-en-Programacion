# Fase 5 – Análisis Raster y Despliegue

## 🎯 Objetivo de la Fase
Implementar el motor de análisis raster: conexión a archivos GeoTIFF (COG preferido), recorte por geometría del lote (masking), cálculo de estadísticas por tipo de recurso forrajero (resource_1..4), guardado de resultados en BD, y exposición de endpoints de consulta. Completar con despliegue a producción (Docker, reverse proxy, HTTPS, variables de entorno, monitoreo básico). **Incluye: Celery obligatorio, cache de resultados, versionado de raster, control de concurrencia, política de almacenamiento, reporte PDF mejorado.**

## 📦 Artefactos Generados en esta Fase
- `backend/app/schemas/analysis.py` – Pydantic: `AnalysisCreate`, `AnalysisRead`, `AnalysisListResponse`, `ResourceTypeEnum`, `AnalysisCacheCheck`, `ConcurrentAnalysisError`, `AnalysisReportConfig`
- `backend/app/routers/analyses.py` – Endpoints: `POST /analyses`, `POST /analyses/check-cache`, `GET /analyses`, `GET /analyses/{id}`, `GET /analyses/timeseries`, `GET /lots/{lot_id}/analyses`, `POST /analyses/{id}/report`
- `backend/app/services/raster_service.py` – Núcleo: `analyze_lot_resource()`, `clip_raster_to_geometry()`, `calculate_statistics()`, `get_raster_path()`, `_check_cache()`, `_check_concurrent_analysis()`, `_compute_geometry_hash()`
- `backend/app/workers/celery_app.py` – Celery + Redis config + beat schedule
- `backend/app/workers/raster_tasks.py` – Tasks Celery: `run_analysis_task` (cache, concurrencia, versionado, storage), `check_analysis_cache`, `update_all_raster_layers`, `generate_alerts_for_anomalies`
- `backend/app/workers/periodic_tasks.py` – Tareas periódicas: `update_all_raster_layers`, `generate_alerts_for_anomalies`, `cleanup_old_reports`, `cleanup_stale_analyses`
- `backend/app/services/notification_service.py` – Canales: email, push, webhook
- `backend/app/utils/report_generator.py` – PDF con logo, metadata, leyenda, fecha, parámetros
- `backend/app/core/raster_config.py` – `RASTER_CATALOG` con versionado (`version`, `date`, `metadata`)
- `backend/tests/test_raster.py` – Tests: cache, concurrencia, versionado, area mínima, ownership, filtros
- `docker-compose.prod.yml` – nginx, backend, frontend, postgres, redis, celery-worker, celery-beat, prometheus, grafana, certbot
- `nginx/nginx.conf` – Reverse proxy + SSL + rate limiting + security headers
- `backend/Dockerfile.prod`, `frontend/Dockerfile.prod` – Multi-stage builds
- `monitoring/prometheus.yml`, `monitoring/grafana/datasources.yml` – Monitoreo

## 🧩 Detalle Técnico

### Backend (FastAPI + SQLModel + Celery)
**Endpoints creados:**
| Método | Ruta | Body/Params | Response | Descripción |
|--------|------|-------------|----------|-------------|
| POST | `/analyses` | `AnalysisCreate{lot_id, resource_type, store_clipped_raster}` | `AnalysisRead` (202) | Inicia análisis async (Celery), cache/concurrencia/versionado |
| POST | `/analyses/check-cache` | `{lot_id, resource_type}` | `AnalysisCacheCheck` | Verifica cache antes de crear análisis |
| GET | `/analyses` | `?lot_id=&resource_type=&status=&page=&size=` | `AnalysisListResponse` | Historial paginado con filtros |
| GET | `/analyses/timeseries` | `?lot_id=&resource_type=` | `TimeSeriesResponse` | Serie temporal con versionado |
| GET | `/analyses/{id}` | — | `AnalysisRead` | Detalle completo con versionado |
| POST | `/analyses/{id}/report` | `config` | `dict{pdf_url}` | Genera reporte PDF |

**Esquema `AnalysisRead` (con mejoras):**
```python
class AnalysisRead(BaseModel):
    id: UUID
    lot_id: UUID
    resource_type: ResourceTypeEnum
    average_rate: float
    min_value: float | None
    max_value: float | None
    std_dev: float | None
    percentiles: dict[str, float] | None
    raster_file_reference: str
    raster_version: str              # NUEVO: ej "v2024.1"
    raster_date: datetime            # NUEVO: fecha del raster
    clipped_raster_path: str | None  # NUEVO: si store_clipped_raster=True
    store_clipped_raster: bool       # NUEVO: política almacenamiento
    lot_geometry_hash: str           # NUEVO: SHA256 geometría para cache
    analyzed_at: datetime
    status: Literal["pending","processing","completed","failed"]
    error_message: str | None
```

**Nuevos esquemas:**
```python
class AnalysisCreate(BaseModel):
    lot_id: UUID
    resource_type: ResourceTypeEnum
    store_clipped_raster: bool = False  # NUEVO: política almacenamiento

class AnalysisCacheCheck(BaseModel):
    cached: bool
    analysis: AnalysisRead | None
    message: str

class ConcurrentAnalysisError(BaseModel):
    error: str = "Ya existe un análisis en curso..."
    existing_analysis_id: UUID
    existing_status: str
    retry_after_seconds: int = 30
```

**Servicio `raster_service.py` (mejoras):**
- `_compute_geometry_hash(geometry: dict) -> str`: SHA256 para cache
- `_check_cache(session, lot_id, resource_type, geometry_hash, raster_version) -> Analysis|None`: Cache lookup
- `_check_concurrent_analysis(session, lot_id, resource_type) -> Analysis|None`: Concurrency check
- `analyze_lot_resource(...)`: 
  - Verifica cache → retorna existente si coincide (misma geometría + raster_version)
  - Verifica concurrencia → 409 si hay análisis PENDING/PROCESSING mismo lote+recurso
  - Ejecuta análisis → guarda `raster_version`, `raster_date`, `lot_geometry_hash`, `store_clipped_raster`
  - Opcional: guarda raster recortado (`clipped_raster_path`) si `store_clipped_raster=True`
- `run_analysis_task()`: Task Celery con retry, cache check, concurrency check

**Celery Tasks (`raster_tasks.py`):**
- `run_analysis_task(analysis_id)`: Task principal con retry, cache hit, concurrency check
- `check_analysis_cache(lot_id, resource_type, geometry_hash, raster_version)`: Cache check síncrono
- `update_all_raster_layers()`: Daily, actualiza capraster desde GEE/Sentinel
- `generate_alerts_for_anomalies()`: Daily, detecta anomalías (<10% histórico)
- `cleanup_stale_analyses()`: Hourly, marca FAILED análisis >2h en PROCESSING
- `generate_analysis_report(analysis_id)`: Genera PDF

**Periodic Tasks (`periodic_tasks.py`):**
- `update_all_raster_layers()`: Daily 2AM (Celery Beat)
- `generate_alerts_for_anomalies()`: Daily 3AM
- `cleanup_old_reports()`: Weekly, >30 días
- `cleanup_stale_analyses()`: Hourly, >2h en PROCESSING

**Cache & Concurrencia:**
- **Cache key**: `(lot_id, resource_type, geometry_hash, raster_version)`
- **Concurrency lock**: Max 1 análisis PENDING/PROCESSING por `(lot_id, resource_type)`
- **Lock TTL**: 5 min (auto-liberación si worker muere)

**Versionado Raster:**
- `raster_version`: string (ej: "v2024.1", "v2024.2")
- `raster_date`: datetime del raster
- Guardados en cada `Analysis` para trazabilidad

**Política de Almacenamiento:**
- `store_clipped_raster: bool` (default False)
- `False`: Solo estadísticas en BD (bajo almacenamiento)
- `True`: Estadísticas + raster recortado GeoTIFF en `/data/rasters/clipped/`

**Reporte PDF (`report_generator.py`):**
- Portada: logo, título, fecha
- Metadata: análisis ID, lote, usuario, fechas, raster_version, raster_date, hash geometría
- Parámetros: recurso, raster origen, versión, hash geometría, store_clipped
- Estadísticas: media, min, max, std, percentiles (p25, p50, p75, p90, p95), count
- Leyenda por recurso
- Mapa del lote (placeholder)

### Frontend (React + TypeScript)
**Nuevos endpoints en `analysesApi.ts`:**
- `checkCache(lot_id, resource_type)`: POST `/analyses/check-cache`

**Componentes Results actualizados:**
- `AnalysisDetail`: Muestra `raster_version`, `raster_date`, `lot_geometry_hash`, `store_clipped_raster`
- `AnalysisHistoryPage`: Botón "Analizar" → llama `checkCache` primero → si cached muestra existente, sino crea nuevo

### Base de Datos (PostgreSQL/PostGIS)
**Migración 004** (`004_auth_improvements.py`): Campos auth
**Migración 005** (`005_lot_versions.py`): Tabla `lot_versions`
**Migración 006** (nueva): Tabla `analyses` con campos:
- `raster_version` VARCHAR(100) NOT NULL
- `raster_date` TIMESTAMPTZ NOT NULL
- `clipped_raster_path` TEXT NULL
- `store_clipped_raster` BOOLEAN DEFAULT FALSE
- `lot_geometry_hash` VARCHAR(64) NOT NULL
- Índices: `(lot_id, resource_type, status)`, `lot_geometry_hash`, `raster_version`

### Despliegue (Docker + Nginx + HTTPS + Celery)
**`docker-compose.prod.yml` servicios:**
- `nginx`: Reverse proxy + SSL (Let's Encrypt) + rate limiting (api:10r/s, auth:5r/m)
- `backend`: Gunicorn 4 workers Uvicorn
- `frontend`: Nginx static (SPA fallback)
- `postgres`: PostgreSQL 15 + PostGIS
- `redis`: Redis 7 (Celery broker/result backend)
- `celery-worker`: 2 workers, queue `analysis`
- `celery-beat`: Scheduler (daily 2AM/3AM)
- `prometheus`: Scrape `/metrics`
- `grafana`: Dashboards auto-provisioned
- `certbot`: Let's Encrypt auto-renewal

**Nginx config:** Rate limiting, security headers, SSL, proxy_pass

### Monitoreo
**Prometheus scrape configs:** backend, node, postgres, redis, nginx
**Grafana dashboards:** Requests, latency, DB pool, analysis queue, cache hit rate

## ✅ Criterios de Aceptación de la Fase
- [ ] `POST /analyses` con `lot_id` válido + `resource_type` → 202, analysis creado status="pending", **cache check + concurrency check**
- [ ] **Cache hit**: mismo lote + geometría + raster_version → retorna existente (200) sin reprocesar
- [ ] **Concurrencia**: 2do POST mismo lote+recurso → 409 con `existing_analysis_id` + `retry_after_seconds`
- [ ] **Versionado**: `raster_version` + `raster_date` guardados en Analysis
- [ ] **Cache hit**: background task detecta cache → copia resultados sin reprocesar
- [ ] **Storage policy**: `store_clipped_raster=True` → guarda GeoTIFF recortado en `/data/rasters/clipped/`
- [ ] **Celery**: `run_analysis_task` ejecuta en worker, retry 3x, `update_all_raster_layers` daily via Beat
- [ ] `POST /analyses/check-cache` → `{cached: true, analysis: ...}` si existe
- [ ] `GET /analyses` filtros: `status`, `resource_type` funcionan
- [ ] Frontend: botón "Analizar" → `check-cache` → si cached muestra existente, sino crea + polling
- [ ] `POST /analyses/{id}/report` → genera PDF con logo, metadata, leyenda, fecha, parámetros
- [ ] `docker compose -f docker-compose.prod.yml up -d` levanta 10 servicios en < 3 min
- [ ] HTTPS válido (Let's Encrypt), Prometheus + Grafana funcionando
- [ ] Tests: `pytest backend/tests/test_raster.py -v` → todos pasan (cache, concurrencia, versionado, ownership)
- [ ] `make lint` / `npm run lint` / `npm run build` pasan en producción

## 🔗 Dependencias con otras Fases
- **Requisito previo**: Fase 1 (DB, modelos), Fase 2 (auth, ownership, lockout), Fase 3 (lotes + geometría + versionado + soft delete), Fase 4 (MapView + validación geometría)
- **Habilita**: MVP completo listo para usuarios finales; base para futuras fases (alertas push, API pública, mobile app, series temporales avanzadas, comparación campañas, GEE integration)

## 📋 Resumen de Mejoras Implementadas vs Original

| Mejora | Original | Implementado |
|--------|----------|--------------|
| **Celery** | BackgroundTasks opcional | **Obligatorio** (config, tasks, beat, workers) |
| **Cache** | No | **SHA256 geometry_hash + raster_version** |
| **Concurrencia** | No | **Lock por lote+recurso, 409 + retry_after** |
| **Versionado raster** | No | **raster_version + raster_date en Analysis** |
| **Storage policy** | No | **store_clipped_raster (bool), clipped_raster_path** |
| **Reporte PDF** | Básico | **Logo, metadata, leyenda, fecha, parámetros, mapa** |
| **Tareas periódicas** | No | **Celery Beat: update rasters, alerts, cleanup** |
| **Monitoreo** | Básico | **Prometheus + Grafana dashboards** |
| **Tests** | Básicos | **Cache, concurrencia, versionado, ownership, filtros** |