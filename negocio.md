# Reglas de Negocio - GeoForraje 1.0

## 📜 Normativas y Restricciones del Sistema

### 1. Validación de Geometría (Business Rule BR-01)

| Regla | Descripción | Implementación |
|-------|-------------|----------------|
| **Geometría obligatoria** | Todo lote debe tener geometría Polygon válida | Validación en `lot_service.validate_geometry()` |
| **Anillo exterior CCW** | El anillo exterior debe estar en sentido antihorario (WGS84 estándar) | Validación con `shapely.orient(geom, sign=1.0)` |
| **Anillos interiores CW** | Los anillos interiores (huecos) deben estar en sentido horario | Validación implícita por `orient()` |
| **Mínimo 4 puntos** | El anillo exterior debe tener al menos 4 coordenadas (cerrado) | Validación en esquema Pydantic + Shapely |
| **No self-intersection** | La geometría no debe tener auto-intersecciones | `shapely.make_valid()` o error 400 |
| **SRID 4326 (WGS84)** | Todas las coordenadas deben ser [lon, lat] | Validación en `ST_SetSRID(ST_GeomFromGeoJSON)` |

### 2. Reglas de Autenticación (Business Rule BR-02)

| Regla | Descripción | Implementación |
|-------|-------------|----------------|
| **Access Token 15 min** | El token de acceso expira en 15 minutos | `ACCESS_TOKEN_EXPIRE_MINUTES = 15` en config |
| **Refresh Token 7 días** | El token de refresco expira en 7 días | `REFRESH_TOKEN_EXPIRE_DAYS = 7` en config |
| **Refresh Token Rotation** | Cada uso del refresh token invalida el anterior y emite nuevo par | Lógica en `routers/auth.py` `POST /auth/refresh` |
| **Máximo 1 refresh activo** | No se permiten múltiples refresh tokens simultáneos para el mismo usuario | Controlado por la lógica de invalidación |
| **401 credentials inválidas** | Login con password incorrecto retorna 401 con mensaje específico | `raise HTTPException(401, "Credenciales inválidas")` |

### 3. Reglas de Negocio de Lotes (Business Rule BR-03)

| Regla | Descripción | Implementación |
|-------|-------------|----------------|
| **Propiedad de usuario** | Un usuario solo puede modificar/eliminar sus propios lotes | Filtro `Lot.user_id == current_user.id` en todos los endpoints |
| **Nombre único por usuario** | El nombre del lote debe ser único dentro del mismo usuario (no global) | Validación en `lot_service.create_lot()` y `update_lot()` |
| **Área calculada automáticamente** | `area_ha` se calcula al crear/actualizar, no por usuario | `lot_service.calculate_area_ha()` en `lot_service.py` |
| **Geometría en WKB para PostGIS** | La geometría se almacena como `geometry` column tipo PostGIS | `ST_SetSRID(ST_GeomFromGeoJSON)` en `lot_service.py` |
| **Eliminación en cascada** | Al eliminar un lote, se borran todos sus analyses asociados | `ondelete="CASCADE"` en modelo SQLModel o lógica en `lot_service.delete_lot()` |

### 4. Reglas de Análisis (Business Rule BR-04)

| Regla | Descripción | Implementación |
|-------|-------------|----------------|
| **4 recursos forrajeros** | Solo se pueden seleccionar tipos: `resource_1`, `resource_2`, `resource_3`, `resource_4` | Validación en esquema `AnalysisCreate.resource_type` |
| **Tasa promedio debe ser positiva** | `average_rate > 0` | Validación en esquema Pydantic `AnalysisCreate` |
| **Status workflow** | Los analyses siguen flujo: `pending` → `processing` → `completed`/`failed` | Controlado en el backend, no permite saltos de fase |
| **Error message obligatorio si falla** | Si `status = 'failed'`, debe tener `error_message` | Validación en esquema `AnalysisCreate`/`AnalysisRead` |

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

### 7. Reglas de Seguraity Adicionales (Business Rule BR-07)

| Regla | Descripción | Implementación |
|-------|-------------|----------------|
| **JWT en header Authorization** | `Authorization: Bearer <access_token>` | Interceptor en `authApi.ts` frontend + middleware FastAPI |
| **Token type validation** | Middleware verifica que `type = "access"` en el payload | `decode_token()` en `security.py` |
| **Refresh token reuse rejection** | Intentos de usar un refresh token ya invalidado retornan 401 | Lógica en `POST /auth/refresh` |
| **Logout invalida tokens** | `POST /auth/logout` remueve store + localStorage + redirect `/login` | `authStore.logout()` + `window.location.href` |

## 📌 Resumen Ejecutivo de Reglas

| Categoría | Regla Crítica | Prioridad |
|-----------|---------------|-----------|
| Geometría | Polygon válido, CCW, SRID 4326 | 🔴 Crítica |
| Autenticación | JWT rotation, 15min/7d expiración | 🔴 Crítica |
| Lotes | Propiedad de usuario, nombre único por usuario | 🟠 Alta |
| Análisis | Workflow de status, 4 recursos válidos | 🟠 Alta |
| Mapa | Capas base, pm toolbar config | 🟢 Media |
| Seguridad | JWT header, logout cleanup | 🟢 Alta |