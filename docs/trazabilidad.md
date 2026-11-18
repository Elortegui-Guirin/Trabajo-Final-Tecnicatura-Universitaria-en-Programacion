# Matriz de Trazabilidad - GeoForraje 1.0

Vincula cada requerimiento ([`requerimientos.md`](requerimientos.md)) con sus reglas de negocio ([`negocio.md`](negocio.md)), los endpoints ([`API_SPECS.md`](API_SPECS.md)), las tablas ([`diagrama_er.md`](diagrama_er.md)), los módulos de código y los tests que lo verifican. Actualizada al 18/11/2026.

## 1. Requerimientos funcionales

| Req. | Reglas de negocio | Endpoints | Tablas | Backend | Frontend | Tests |
|------|-------------------|-----------|--------|---------|----------|-------|
| **FR-01** Registro | RN-AUTH-01 | `POST /auth/register`, `POST /auth/verify-email`, `POST /auth/resend-verification` | `users` | `routers/auth.py`, `core/security.py`, `schemas/auth.py` | `RegisterPage`, `authApi` | `test_register_user` |
| **FR-02** Autenticación y sesión | RN-AUTH-02 a RN-AUTH-07 | `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `POST /auth/forgot-password`, `POST /auth/reset-password` | `users` (`refresh_token_jti`, `failed_login_attempts`, `locked_until`, `reset_token`) | `routers/auth.py`, `core/security.py`, `models/user.py` | `LoginPage`, `authApi` (interceptor de refresh), `authStore`, `Layout` (logout) | `test_login_valid`, `test_login_invalid_password`, `test_token_refresh`, `test_logout_invalidates_refresh_token` |
| **FR-03** Gestión de lotes | RN-GEO-01 a RN-GEO-06, RN-LOT-01 a RN-LOT-05 | `POST /lots`, `GET /lots`, `GET /lots/{id}`, `GET /lots/{id}/versions`, `PATCH /lots/{id}`, `DELETE /lots/{id}`, `POST /lots/{id}/restore` | `lots`, `lot_versions` | `routers/lots.py`, `services/lot_service.py`, `models/lot.py`, `models/lot_version.py` | `LotsPage`, `LotList`, `LotFormPage`, `LotForm`, `LotDetailPage`, `LotDetail`, `useLots` | `test_create_lot`, `test_create_lot_invalid_geometry`, `test_create_lot_area_too_small`, `test_create_lot_duplicate_name`, `test_create_lot_creates_version`, `test_list_lots`, `test_list_lots_advanced_filters`, `test_get_lot`, `test_update_lot_name`, `test_update_lot_geometry_creates_version`, `test_update_lot_geometry_area_too_small`, `test_soft_delete_lot`, `test_restore_lot`, `test_soft_delete_preserves_analyses`, `test_version_history_ordering` |
| **FR-04** Mapa interactivo | RN-MAP-01 a RN-MAP-03, RN-GEO-06, RN-GEO-07 | (cliente) usa `POST /lots` y `PATCH /lots/{id}` | — | — | `MapEditor`, `MapView`, `useGeoJSON`, `LotForm` | Prueba manual (sin tests de frontend) |
| **FR-05** Análisis forrajero | RN-ANA-01 a RN-ANA-09 | `POST /analyses`, `POST /analyses/check-cache`, `GET /analyses`, `GET /analyses/{id}`, `GET /analyses/lots/{lot_id}/analyses`, `GET /analyses/timeseries` | `analyses` | `routers/analyses.py`, `services/raster_service.py`, `core/raster_config.py`, `workers/raster_tasks.py`, `workers/celery_app.py` | `AnalysisHistoryPage`, `AnalysisList`, `AnalysisDetailPage`, `AnalysisDetail`, `AnalysisChart`, `useAnalyses` | `test_create_analysis`, `test_create_analysis_checks_concurrency`, `test_check_analysis_cache`, `test_analysis_versioning`, `test_analysis_geometry_hash`, `test_analysis_store_clipped_raster`, `test_list_analyses_with_filters`, `test_get_analysis_detail`, `test_get_lot_analyses`, `test_analysis_timeseries` |
| **FR-06** Protección de rutas y datos | RN-AUTH-08, RN-LOT-01 | `GET /auth/me` y todos los endpoints privados | `users` | `api/deps.py` (`get_current_user`, `get_current_active_user`) | `PrivateRoute` en `App.tsx`, interceptor de `authApi` | `test_get_me_with_token`, `test_lot_ownership_isolation`, `test_analysis_ownership_isolation` |
| **FR-07** Panel de control | — | `GET /lots`, `GET /analyses` | `lots`, `analyses` | (reutiliza routers de lotes y análisis) | `DashboardPage` | Prueba manual |
| **FR-08** Exportar / importar | — | — | — | — | — | Pendiente (no implementado) |

## 2. Reglas críticas y cómo se verifican

Las reglas que el checklist del TFI pide demostrar (concurrencia, seguridad, estados, algoritmos), con la evidencia de cada una.

| Regla | Qué se comprueba | Evidencia |
|-------|------------------|-----------|
| RN-ANA-07 Concurrencia | Un segundo análisis del mismo lote y especie, mientras hay uno en curso, devuelve 409 | `test_create_analysis_checks_concurrency` |
| RN-ANA-08 Cache | El mismo lote, especie, geometría y versión de mapa no se recalcula | `test_check_analysis_cache`, `test_analysis_geometry_hash` |
| RN-ANA-05 Estados | `pending` → `processing` → `completed`, sobre el mismo registro | `test_create_analysis` (estado inicial) + prueba manual del worker (log del 11/11: completado en 0,45 s) |
| RN-ANA-02 / RN-ANA-03 Cálculo | El promedio ignora NoData y valores negativos | Prueba con datos simulados (40, 50, 60 → 50, y no 16,7) y análisis real: alfalfa 9,38 kg MS/ha/día. Falta un test automático |
| RN-ANA-04 Lotes chicos | Un lote más chico que un píxel usa los píxeles que toca | Prueba sobre los mapas reales. Falta un test automático |
| RN-AUTH-03 / RN-AUTH-04 Rotación | Un refresh token reutilizado devuelve 401 | `test_token_refresh` |
| RN-AUTH-06 Logout | Después del logout, el refresh token devuelve 401 | `test_logout_invalidates_refresh_token` |
| RN-AUTH-07 Bloqueo | 5 contraseñas incorrectas → 423; más de 10 intentos por IP → 429 | Prueba manual (se disparó el 429 el 11/11). Falta un test automático |
| RN-LOT-01 Propiedad | Un usuario no ve lotes ni análisis de otro | `test_lot_ownership_isolation`, `test_analysis_ownership_isolation` |
| RN-LOT-02 Nombre único | Un nombre repetido (sin distinguir mayúsculas) → 422 | `test_create_lot_duplicate_name` |
| RN-LOT-04 / RN-LOT-05 Eliminación lógica | El lote eliminado se puede restaurar y sus análisis se conservan | `test_soft_delete_lot`, `test_restore_lot`, `test_soft_delete_preserves_analyses` |
| RN-GEO-02 / RN-GEO-05 Geometría | Polígono inválido o área fuera de rango → 422 | `test_create_lot_invalid_geometry`, `test_create_lot_area_too_small`, `test_update_lot_geometry_area_too_small` |

## 3. Requerimientos no funcionales

| NFR | Implementación | Evidencia |
|-----|----------------|-----------|
| NFR-04 Análisis < 5 s | Worker Celery + Rasterio | Log del worker: 0,45 s |
| NFR-05 bcrypt | `core/security.py` | Columna `users.hashed_password` |
| NFR-06 / NFR-07 JWT y rotación | `core/security.py`, `users.refresh_token_jti` | `test_token_refresh`, `test_logout_invalidates_refresh_token` |
| NFR-09 Límite de intentos | `check_rate_limit()`, `User.record_failed_login()` | Prueba manual |
| NFR-10 Validación de geometría | `lot_service.validate_geometry()` | `test_create_lot_invalid_geometry` |
| NFR-12 Procesamiento asíncrono | Celery + Redis | `docker-compose.yml` (servicio `celery-worker`) |
| NFR-13 Entorno reproducible | Docker Compose | README, sección "Inicio rápido" |
| NFR-15 a NFR-17 Observabilidad | `/health`, `/ready`, `/metrics`, `/docs` | `test_health_check`, `test_readiness_check` |
| NFR-18 Migraciones | Alembic | Parcial: migraciones desactualizadas |
| NFR-20 Tests | `pytest` | 35 tests de backend |
| NFR-21 CI | — | Pendiente |
