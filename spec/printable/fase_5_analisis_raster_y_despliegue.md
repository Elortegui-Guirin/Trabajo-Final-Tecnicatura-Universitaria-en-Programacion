# Fase 5 – Análisis Raster y Despliegue

## 🎯 Objetivo de la Fase
Implementar el motor de análisis raster: conexión a archivos GeoTIFF (COG preferido), recorte por geometría del lote (masking), cálculo de estadísticas por tipo de recurso forrajero (resource_1..4), guardado de resultados en BD, y exposición de endpoints de consulta. Completar con despliegue a producción (Docker, reverse proxy, HTTPS, variables de entorno, monitoreo básico).

## 📦 Artefactos Generados en esta Fase
- `backend/app/schemas/analysis.py` – Pydantic: `AnalysisCreate`, `AnalysisRead`, `AnalysisListResponse`, `ResourceTypeEnum`
- `backend/app/routers/analyses.py` – Endpoints: `POST /analyses`, `GET /analyses`, `GET /analyses/{id}`, `GET /lots/{lot_id}/analyses`
- `backend/app/services/raster_service.py` – Núcleo: `analyze_lot_resource()`, `clip_raster_to_geometry()`, `calculate_statistics()`, `get_raster_path()`
- `backend/app/workers/raster_worker.py` – Background task (FastAPI `BackgroundTasks`) o Celery task: `run_analysis_task(analysis_id)`
- `backend/app/core/raster_config.py` – Config: `RASTER_CATALOG` (dict resource_type → path/url GeoTIFF), band mapping, nodata handling
- `backend/tests/test_raster.py` – Tests: clip, stats, resource types, error handling (archivo faltante, geometría fuera de bounds)
- `frontend/src/modules/results/` – Módulo resultados:
  - `components/AnalysisList.tsx` – Historial por lote: tabla (fecha, recurso, tasa, acción ver)
  - `components/AnalysisDetail.tsx` – Detalle: métricas (media, min, max, std, percentiles), histograma (Recharts), mapa mini (resultado recortado)
  - `components/AnalysisChart.tsx` – Gráfico barras/línea comparativo temporal por recurso
  - `hooks/useAnalyses.ts` – Queries: `useAnalyses(lotId)`, `useAnalysis(id)`, `useRunAnalysis(lotId, resourceType)`
  - `api/analysesApi.ts` – Cliente tipado
  - `pages/AnalysisHistoryPage.tsx` – Lista análisis del lote seleccionado
  - `pages/AnalysisDetailPage.tsx` – Vista detalle + botón "Descargar reporte PDF"
- `backend/app/utils/report_generator.py` – Genera PDF reporte (WeasyPrint / ReportLab): portada, mapa, tabla métricas, gráfico
- `docker-compose.prod.yml` – Producción: nginx reverse proxy, certbot (Let's Encrypt), backend (gunicorn+uvicorn workers), frontend (nginx static), postgres, redis (Celery)
- `nginx/nginx.conf` – Config proxy: rate limiting, gzip, headers seguridad, proxy_pass backend/frontend
- `backend/Dockerfile.prod` – Multi-stage: builder (poetry) → runtime (slim, non-root user)
- `frontend/Dockerfile.prod` – Multi-stage: builder (npm ci + build) → nginx alpine
- `.github/workflows/deploy.yml` – CD: build images → push registry → deploy server (ssh/ansible/k8s)
- `monitoring/prometheus.yml` – Scrape config backend `/metrics` (prometheus-fastapi-instrumentator)
- `monitoring/grafana/dashboards/geoforraje.json` – Dashboard: requests, latency, DB pool, analysis queue

## 🧩 Detalle Técnico

### Backend (FastAPI + SQLModel)
**Endpoints creados:**
| Método | Ruta | Body/Params | Response | Descripción |
|--------|------|-------------|----------|-------------|
| POST | `/analyses` | `AnalysisCreate{lot_id, resource_type}` | `AnalysisRead` (202) | Inicia análisis async, retorna analysis_id + status="pending" |
| GET | `/analyses` | `?lot_id=&resource_type=&page=1&size=20` | `AnalysisListResponse` | Historial paginado con filtros |
| GET | `/analyses/{id}` | — | `AnalysisRead` | Detalle análisis completo |
| GET | `/lots/{lot_id}/analyses` | — | `AnalysisListResponse` | Shortcut para frontend |

**Esquema `AnalysisRead`:**
```python
class AnalysisRead(BaseModel):
    id: UUID
    lot_id: UUID
    resource_type: ResourceTypeEnum
    average_rate: float
    min_value: float | None
    max_value: float | None
    std_dev: float | None
    percentiles: dict[str, float] | None  # {"p25": ..., "p50": ..., "p75": ...}
    raster_file_reference: str
    analyzed_at: datetime
    status: Literal["pending", "processing", "completed", "failed"]
    error_message: str | None
```

**Servicio `raster_service.py`:**
```python
def analyze_lot_resource(lot_id: UUID, resource_type: ResourceTypeEnum, session: Session) -> Analysis:
    # 1. Obtener lote + geometría (WKB → Shapely Polygon)
    # 2. Resolver path GeoTIFF desde RASTER_CATALOG[resource_type]
    # 3. Abrir raster (rasterio.open), leer CRS, transform
    # 4. Reproyectar geometría lote a CRS del raster (pyproj.Transformer)
    # 5. clip: rasterio.mask.mask(dataset, [geom], crop=True, nodata=np.nan)
    # 6. Calcular stats: mean, min, max, std, percentiles (np.nanpercentile)
    # 7. Crear Analysis record con status="completed", guardar
    # 8. Retornar Analysis
```

**Catálogo raster (`raster_config.py`):**
```python
RASTER_CATALOG: dict[ResourceTypeEnum, RasterSource] = {
    "resource_1": RasterSource(path="/data/rasters/resource_1.tif", band=1, nodata=-9999, description="Biomasa verde"),
    "resource_2": RasterSource(path="/data/rasters/resource_2.tif", band=1, nodata=-9999, description="Cobertura suelo"),
    "resource_3": RasterSource(path="/data/rasters/resource_3.tif", band=1, nodata=-9999, description="Índice vegetación"),
    "resource_4": RasterSource(path="/data/rasters/resource_4.tif", band=1, nodata=-9999, description="Humedad suelo"),
}
```
- Soporta rutas locales, URLs (HTTP/S3 via `rasterio.open("s3://...")`), COG (Cloud Optimized GeoTIFF)

**Background processing:**
- `POST /analyses` → `BackgroundTasks.add_task(run_analysis_task, analysis_id)`
- `run_analysis_task()`: actualiza status → "processing" → llama `analyze_lot_resource()` → "completed" o "failed" + error_message
- Opcional Celery + Redis para colas persistentes, retries, escalado horizontal

### Frontend (React + TypeScript)
**Componentes Results:**
- `AnalysisList`: TanStack Table, columnas: fecha, recurso (badge color), tasa media (formato 2 decimales), estado, acción "Ver"
- `AnalysisDetail`: Grid métricas (Media, Min, Max, Desv.Std, P25/P50/P75), `AnalysisChart` (histograma valores píxel), `MapView` mini con capa resultado (estilo choropleth)
- `AnalysisChart`: Recharts `BarChart` / `LineChart` comparando análisis temporales del mismo lote+recurso
- `useRunAnalysis`: Mutation `POST /analyses` → polling `GET /analyses/{id}` cada 3s hasta status completed/failed → invalidar queries lista

**Estado (TanStack Query):**
```typescript
const analysisKeys = {
  all: ['analyses'] as const,
  list: (filters: AnalysisFilters) => [...analysisKeys.all, 'list', filters] as const,
  detail: (id: string) => [...analysisKeys.all, 'detail', id] as const,
};

// Polling hook
function useAnalysisPolling(id: string, enabled: boolean) {
  return useQuery({
    queryKey: analysisKeys.detail(id),
    queryFn: () => analysesApi.get(id),
    refetchInterval: (data) => data?.status === 'pending' || data?.status === 'processing' ? 3000 : false,
    enabled,
  });
}
```

### Base de Datos (PostgreSQL/PostGIS)
- **Migración 004** (extensión análisis):
  - `ALTER TABLE analyses ADD COLUMN status VARCHAR(20) DEFAULT 'pending';`
  - `ALTER TABLE analyses ADD COLUMN error_message TEXT;`
  - `ALTER TABLE analyses ADD COLUMN min_value NUMERIC(10,4), max_value NUMERIC(10,4), std_dev NUMERIC(10,4), percentiles JSONB;`
  - Índice `idx_analyses_status` para colas de procesamiento
  - Check constraint `status IN ('pending','processing','completed','failed')`

### Despliegue (Docker + Nginx + HTTPS)
**Arquitectura producción:**
```
Internet → [Nginx:443/80] → 
  ├── /api/* → Backend (gunicorn -w 4 -k uvicorn.workers.UvicornWorker)
  ├── / → Frontend (Nginx static files, try_files $uri /index.html)
  └── /.well-known/acme-challenge/ → Certbot
```
**Variables entorno producción (`.env.prod`):**
- `DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/geoforraje`
- `JWT_SECRET=...` (32+ chars, rotado)
- `CORS_ORIGINS=https://geofarraje.example.com`
- `RASTER_DATA_PATH=/data/rasters` (volume montado)
- `SENTRY_DSN=...` (opcional error tracking)

**Healthchecks:**
- Backend: `GET /health` (DB connection + raster catalog accesible)
- Frontend: Nginx status 200 en `/`
- Postgres: `pg_isready`

## ✅ Criterios de Aceptación de la Fase
- [ ] `POST /analyses` con `lot_id` válido + `resource_type` → 202, analysis creado status="pending"
- [ ] Background task completa análisis: `average_rate` calculado, percentiles guardados, status="completed"
- [ ] Análisis con geometría fuera de bounds del raster → status="failed", error_message descriptivo
- [ ] `GET /analyses` paginado + filtros (lot_id, resource_type) funciona
- [ ] Frontend: botón "Analizar" en detalle lote → muestra loading → polling → muestra resultado completo
- [ ] Frontend: histograma (Recharts) renderiza distribución valores píxel del recorte
- [ ] Frontend: mini-mapa muestra recorte raster estilizado (choropleth) sincronizado con geometría lote
- [ ] `docker compose -f docker-compose.prod.yml up -d` levanta stack completo en < 3 min
- [ ] HTTPS válido (Let's Encrypt) → `curl -I https://geofarraje.example.com` → 200, cert válido
- [ ] Prometheus scrapea `/metrics` del backend; Grafana dashboard muestra métricas clave
- [ ] Tests backend: `pytest backend/tests/test_raster.py -v` → todos pasan
- [ ] `make lint` / `npm run lint` / `npm run build` pasan en producción

## 🔗 Dependencias con otras Fases
- **Requisito previo**: Fase 1 (DB, modelos), Fase 2 (auth, ownership), Fase 3 (lotes + geometría validada), Fase 4 (MapView para visualización resultado)
- **Habilita**: MVP completo listo para usuarios finales; base para futuras fases (alertas, API pública, mobile app)