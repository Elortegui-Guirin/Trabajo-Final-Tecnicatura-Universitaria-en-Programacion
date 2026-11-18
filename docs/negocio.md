# Reglas de Negocio - GeoForraje 1.0

Fuente única de las reglas del sistema. Cada regla tiene un identificador (`RN-…`) que se usa en [`trazabilidad.md`](trazabilidad.md) para vincularla con requerimientos, endpoints, tablas, módulos y tests. Si otro documento contradice este, vale este.

## 1. Geometría de los lotes (RN-GEO)

| ID | Regla | Dónde se aplica |
|----|-------|-----------------|
| **RN-GEO-01** | Un lote es **un único polígono** (`Polygon`); no se aceptan multipolígonos, líneas ni puntos | Esquema `GeometryInput` + `lot_service.validate_geometry()` → 422 |
| **RN-GEO-02** | El polígono debe ser válido: cerrado, con al menos 4 coordenadas y sin auto-intersecciones | `validate_geometry()` (Shapely `is_valid`) → 422 |
| **RN-GEO-03** | Coordenadas en WGS84 (EPSG:4326), orden `[lon, lat]` | Se guarda con `from_shape(polygon, srid=4326)` |
| **RN-GEO-04** | Orientación normalizada: anillo exterior antihorario, huecos horarios | `shapely.orient(geom, sign=1.0)` antes de guardar |
| **RN-GEO-05** | Área entre **0,01 ha (100 m²) y 10.000 ha** | `lot_service.validate_area()` → 422 |
| **RN-GEO-06** | El área oficial la calcula el servidor proyectando a la zona UTM del lote; el valor del frontend es solo orientativo | `lot_service.calculate_area_ha()` / `useGeoJSON.calculateAreaHa()` |
| **RN-GEO-07** | Más de 5.000 vértices: el frontend simplifica el polígono antes de enviarlo | `useGeoJSON.simplifyGeometry()` |

## 2. Autenticación y sesión (RN-AUTH)

| ID | Regla | Dónde se aplica |
|----|-------|-----------------|
| **RN-AUTH-01** | El email es único; la contraseña tiene al menos 8 caracteres y se guarda con bcrypt | `UserRegister`, `hash_password()` |
| **RN-AUTH-02** | El access token dura **15 minutos** y el refresh token **7 días** | `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS` |
| **RN-AUTH-03** | **Rotación de refresh token**: cada refresh token lleva un identificador único (`jti`). El servidor guarda solo el vigente en `users.refresh_token_jti`. `POST /auth/refresh` exige que el `jti` coincida, emite un par nuevo y reemplaza el `jti` | `create_refresh_token()`, `POST /auth/refresh` |
| **RN-AUTH-04** | Un refresh token ya usado o reemplazado devuelve **401** | `POST /auth/refresh` |
| **RN-AUTH-05** | Una sola sesión activa por usuario: un nuevo login reemplaza el `jti` y deja sin efecto el refresh token anterior | `POST /auth/login` |
| **RN-AUTH-06** | **Logout en ambos lados**: el servidor borra el `jti` vigente (el refresh token deja de servir) y el frontend borra los tokens y redirige a `/login`. El access token restante vence solo, en hasta 15 minutos | `POST /auth/logout` + `Layout.handleLogout()` |
| **RN-AUTH-07** | 5 contraseñas incorrectas bloquean la cuenta 15 minutos (423). Más de 10 intentos por IP en 15 minutos → 429 | `User.record_failed_login()`, `check_rate_limit()` |
| **RN-AUTH-08** | Las rutas privadas exigen `Authorization: Bearer <access_token>` de tipo `access`, de un usuario activo y no eliminado | `get_current_user()` / `get_current_active_user()` |

## 3. Lotes (RN-LOT)

| ID | Regla | Dónde se aplica |
|----|-------|-----------------|
| **RN-LOT-01** | Cada lote pertenece a un usuario; nadie puede ver ni modificar lotes ajenos (responde 404) | Filtro `Lot.user_id == current_user.id` |
| **RN-LOT-02** | El nombre es único entre los lotes **activos** del usuario, sin distinguir mayúsculas | `lot_service.ensure_unique_name()` → 422 |
| **RN-LOT-03** | Crear un lote genera la **versión 1**; cada cambio de geometría agrega una versión con fecha, usuario y motivo. Un cambio solo de nombre no genera versión | `lot_service.create_lot_version()` |
| **RN-LOT-04** | **Eliminación lógica**: eliminar un lote solo completa `deleted_at`. El lote deja de aparecer en los listados pero se puede restaurar | `lot_service.delete_lot()` / `restore_lot()` |
| **RN-LOT-05** | **Los análisis de un lote eliminado se conservan**: nunca se borran en cascada. Así se mantiene el historial de resultados | Sin `ON DELETE CASCADE` desde `analyses`; `delete_lot()` no toca `analyses` |

## 4. Análisis forrajero (RN-ANA)

| ID | Regla | Dónde se aplica |
|----|-------|-----------------|
| **RN-ANA-01** | Hay 4 especies analizables: Alfalfa (`resource_1`), Festuca (`resource_2`), Raigrás (`resource_3`) y Pastizal natural (`resource_4`) | `ResourceTypeEnum`, `core/raster_config.py` |
| **RN-ANA-02** | El resultado es la **tasa de crecimiento promedio del lote en kg MS/ha/día**, con mínimo, máximo, desvío y percentiles | `raster_service.calculate_statistics()` |
| **RN-ANA-03** | Se ignoran los píxeles NoData y los valores negativos (artefactos del mapa) | `valid_min = 0` en el catálogo |
| **RN-ANA-04** | Se promedian los píxeles cuyo centro cae dentro del lote. Si el lote es más chico que un píxel (~11 ha) y no contiene ningún centro, se usan los píxeles que toca | `analyze_lot_resource()` (reintento con `all_touched=True`) |
| **RN-ANA-05** | Ciclo de vida: `pending` → `processing` → `completed` o `failed`. Lo controla el backend y siempre se actualiza el mismo registro | `POST /analyses` + `run_analysis_task` (Celery) |
| **RN-ANA-06** | Un análisis `failed` siempre tiene `error_message`. Ejemplo: lote fuera del mapa o en zona sin dato (urbana, agua) | `raster_service.run_analysis_task()` |
| **RN-ANA-07** | **Concurrencia**: no puede haber dos análisis en curso del mismo lote y especie; el segundo pedido devuelve **409** | `_check_concurrent_analysis()` |
| **RN-ANA-08** | **Cache**: el mismo lote, especie, geometría (hash SHA-256) y versión de mapa devuelve el análisis ya calculado | `_check_cache()` con `lot_geometry_hash` |
| **RN-ANA-09** | Cada análisis guarda la versión y la fecha del mapa usado, para comparar resultados en el tiempo | `raster_version`, `raster_date` |

## 5. Mapa (RN-MAP)

| ID | Regla | Dónde se aplica |
|----|-------|-----------------|
| **RN-MAP-01** | El mapa siempre tiene una capa base: OpenStreetMap por defecto, satélite (Esri) opcional | `LayersControl` en `MapEditor.tsx` |
| **RN-MAP-02** | Un lote se dibuja como un solo polígono: dibujar otro reemplaza al anterior | `LotLayer` en `MapEditor.tsx` |
| **RN-MAP-03** | El formulario no deja guardar sin un polígono dibujado y válido | `LotForm` + `useGeoJSON.validatePolygon()` |

## 6. Auditoría y trazabilidad de cambios (RN-AUD)

| ID | Regla | Dónde se aplica |
|----|-------|-----------------|
| **RN-AUD-01** | La trazabilidad de los lotes se da por dos vías: el **historial de versiones** de geometría (RN-LOT-03) y la **eliminación lógica** (RN-LOT-04, RN-LOT-05) | `lot_versions`, `lots.deleted_at` |
| **RN-AUD-02** | Los usuarios tampoco se borran físicamente: se marca `deleted_at` y dejan de poder autenticarse | `users.deleted_at`, `get_current_user()` |
| **RN-AUD-03** | La tabla `audit_log` (registro genérico de quién cambió qué) **existe en el modelo pero no se usa en esta versión**; su activación es trabajo futuro | `models/audit_log.py` |
