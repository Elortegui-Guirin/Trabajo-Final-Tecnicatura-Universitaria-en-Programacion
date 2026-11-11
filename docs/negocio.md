# Reglas de Negocio - GeoForraje 1.0

## 📜 Normativas y Restricciones del Sistema

### 1. Validación de Geometría (Business Rule BR-01)

| Regla | Descripción | Implementación |
|-------|-------------|----------------|
| **Geometría obligatoria** | Todo lote debe tener geometría Polygon válida | Validación en `lot_service.validate_geometry()` |
| **Anillo exterior CCW** | El anillo exterior debe estar en sentido antihorario (WGS84 estándar) | Validación con `shapely.orient(geom, sign=1.0)` |
| **Anillos interiores CW** | Los anillos interiores (huecos) deben estar en sentido horario | Validación implícita por `orient()` |
| **Mínimo 4 puntos** | El anillo exterior debe tener al menos 4 coordenadas (cerrado) | Validación en esquema Pydantic + Shapely |
| **No self-intersection** | La geometría no debe tener auto-intersecciones | `geom.is_valid` en `validate_geometry()` → error 422 |
| **SRID 4326 (WGS84)** | Todas las coordenadas deben ser [lon, lat] | Se guarda con `from_shape(polygon, srid=4326)` |
| **Área entre 0,01 y 10.000 ha** | Se rechazan lotes menores a 100 m² o mayores a 10.000 ha | `lot_service.validate_area()` → error 422 |

### 2. Reglas de Autenticación (Business Rule BR-02)

| Regla | Descripción | Implementación |
|-------|-------------|----------------|
| **Access Token 15 min** | El token de acceso expira en 15 minutos | `ACCESS_TOKEN_EXPIRE_MINUTES = 15` en config |
| **Refresh Token 7 días** | El token de refresco expira en 7 días | `REFRESH_TOKEN_EXPIRE_DAYS = 7` en config |
| **Refresh Token Rotation** | Cada uso del refresh token invalida el anterior y emite nuevo par | El `jti` del refresh vigente se guarda en `users.refresh_token_jti`; `POST /auth/refresh` lo compara y lo reemplaza |
| **Máximo 1 refresh activo** | No se permiten múltiples refresh tokens simultáneos para el mismo usuario | Un nuevo login reemplaza `refresh_token_jti` (cierra la sesión anterior) |
| **Bloqueo por intentos fallidos** | 5 contraseñas incorrectas bloquean la cuenta 15 min; más de 10 intentos por IP en 15 min → 429 | `User.record_failed_login()` y `check_rate_limit()` |
| **401 credentials inválidas** | Login con password incorrecto retorna 401 con mensaje específico | `raise HTTPException(401, "Credenciales inválidas")` |

### 3. Reglas de Negocio de Lotes (Business Rule BR-03)

| Regla | Descripción | Implementación |
|-------|-------------|----------------|
| **Propiedad de usuario** | Un usuario solo puede modificar/eliminar sus propios lotes | Filtro `Lot.user_id == current_user.id` en todos los endpoints |
| **Nombre único por usuario** | El nombre del lote debe ser único entre los lotes activos del usuario (sin distinguir mayúsculas) | `lot_service.ensure_unique_name()` en `create_lot()` y `update_lot()` → error 422 |
| **Área calculada automáticamente** | `area_ha` se calcula al crear/actualizar, no por usuario | `lot_service.calculate_area_ha()` en `lot_service.py` |
| **Geometría en WKB para PostGIS** | La geometría se almacena como `geometry` column tipo PostGIS | `geoalchemy2.shape.from_shape()` en `lot_service.py` |
| **Eliminación lógica (soft delete)** | Eliminar un lote solo marca `deleted_at`; sus análisis se conservan y el lote se puede restaurar | `lot_service.delete_lot()` / `restore_lot()` |
| **Historial de versiones** | Crear un lote genera la versión 1; cada cambio de geometría agrega una versión | `lot_service.create_lot_version()` |

### 4. Reglas de Análisis (Business Rule BR-04)

| Regla | Descripción | Implementación |
|-------|-------------|----------------|
| **4 especies forrajeras** | Solo se pueden analizar: Alfalfa (`resource_1`), Festuca (`resource_2`), Raigrás (`resource_3`) y Pastizal natural (`resource_4`) | Enum `ResourceTypeEnum` en `AnalysisCreate.resource_type` |
| **Unidad** | El resultado es la tasa de crecimiento promedio del lote en **kg MS/ha/día** | Catálogo en `core/raster_config.py` |
| **Píxeles válidos** | Se ignoran NoData y valores negativos (artefactos del mapa) | `valid_min=0` en el catálogo, `calculate_statistics()` |
| **Píxeles del lote** | Se promedian los píxeles cuyo centro cae dentro del lote; si el lote es más chico que un píxel (~11 ha), los que toca | `analyze_lot_resource()` (reintento con `all_touched=True`) |
| **Sin datos → falla** | Si el lote cae fuera del mapa o en zona sin dato (urbana, agua), el análisis queda `failed` con mensaje | `analyze_lot_resource()` |
| **Un análisis en curso por lote y especie** | Un segundo pedido mientras hay uno `pending`/`processing` devuelve 409 | `_check_concurrent_analysis()` |
| **Cache** | Mismo lote + especie + geometría + versión de raster → se devuelve el análisis ya calculado | `_check_cache()` con `lot_geometry_hash` |
| **Status workflow** | Los analyses siguen flujo: `pending` → `processing` → `completed`/`failed` | Worker de Celery (`run_analysis_task`), actualiza siempre el mismo registro |
| **Error message obligatorio si falla** | Si `status = 'failed'`, debe tener `error_message` | Se completa en `raster_service.run_analysis_task()` al capturar el error |

### 5. Reglas de Mapa (Business Rule BR-05)

| Regla | Descripción | Implementación |
|-------|-------------|----------------|
| **Capas base obligatorias** | El mapa debe cargar al menos una capa base (OSM por defecto) | `BaseLayers.tsx` en frontend |
| **Toolbar pm.enabled** | `leaflet.pm` solo permite draw polígono, edit, remove, cut | Configuración en `DrawControl.tsx` |
| **Coordenadas [lon, lat]** | GeoJSON debe usar orden WGS84 (lon before lat) | Validación en `validatePolygon()` useGeoJSON hook |
| **Área calculada client-side** | Estimación inmediata del área para feedback rápido | `calculateAreaHa()` useGeoJSON hook (aprox) |
| **Validación definitive server** | El área definitiva se calcula en backend y reemplaza el cliente | `lot_service.calculate_area_ha()` en `lot_service.py` |

### 6. Reglas de Consumo de Recursos (Business Rule BR-06)

| Regla | Descripción | Implementación |
|-------|-------------|----------------|
| **Ciclo de vida analysis** | `pending` → `processing` → (`completed` o `failed`) | Controlado por el backend, no manual |
| **Raster file reference** | Cada analysis debe tener referencia a archivo raster procesado | Campo `raster_file_reference` en esquema `AnalysisRead` |
| **Estadísticas opcionales** | `min_value`, `max_value`, `std_dev`, `percentiles` son opcionales | Solo se calculan si el raster tiene esos datos |

### 7. Reglas de Seguridad Adicionales (Business Rule BR-07)

| Regla | Descripción | Implementación |
|-------|-------------|----------------|
| **JWT en header Authorization** | `Authorization: Bearer <access_token>` | Interceptor en `authApi.ts` frontend + middleware FastAPI |
| **Token type validation** | Middleware verifica que `type = "access"` en el payload | `decode_token()` en `security.py` |
| **Refresh token reuse rejection** | Intentos de usar un refresh token ya invalidado retornan 401 | Lógica en `POST /auth/refresh` |
| **Logout** | El frontend borra store + localStorage y redirige a `/login`; `POST /auth/logout` solo registra el evento | `authStore.logout()` |

## 📌 Resumen Ejecutivo de Reglas

| Categoría | Regla Crítica | Prioridad |
|-----------|---------------|-----------|
| Geometría | Polygon válido, CCW, SRID 4326 | 🔴 Crítica |
| Autenticación | JWT rotation, 15min/7d expiración | 🔴 Crítica |
| Lotes | Propiedad de usuario, nombre único por usuario | 🟠 Alta |
| Análisis | Workflow de status, 4 especies, kg MS/ha/día, píxeles válidos | 🟠 Alta |
| Mapa | Capas base, pm toolbar config | 🟢 Media |
| Seguridad | JWT header, logout cleanup | 🟢 Alta |