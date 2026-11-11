# Documentación de API - GeoForraje 1.0

Basado en OpenAPI/Swagger (`GET /openapi.json`), generado desde el código FastAPI.
La referencia siempre actualizada es **http://localhost:8000/docs**.

---

## 🔗 Endpoints por Módulo

### Autenticación (`/auth`)

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register` | Registrar nuevo usuario | ❌ |
| POST | `/auth/login` | Login, retorna access + refresh tokens | ❌ |
| POST | `/auth/refresh` | Rotar refresh token (el anterior queda inválido) | ❌ |
| GET | `/auth/me` | Usuario actual desde token | ✅ |
| POST | `/auth/logout` | Logout (el frontend borra los tokens) | ❌ |
| POST | `/auth/verify-email` | Verificar email con token | ❌ |
| POST | `/auth/resend-verification` | Reenviar email de verificación | ❌ |
| POST | `/auth/forgot-password` | Pedir token para restablecer contraseña | ❌ |
| POST | `/auth/reset-password` | Restablecer contraseña con token | ❌ |

> En desarrollo los "emails" de verificación y reset se imprimen en los logs del backend (`make logs`).

#### `POST /auth/register`
**Request**:
```json
{
  "email": "usuario@ejemplo.com",
  "password": "password123",
  "full_name": "Juan Pérez"
}
```
**Response 201**:
```json
{
  "id": "6f1c2e0a-...",
  "email": "usuario@ejemplo.com",
  "full_name": "Juan Pérez",
  "created_at": "2026-11-11T12:00:00Z",
  "email_verified": false
}
```
**400** si el email ya está registrado.

#### `POST /auth/login`
**Request**:
```json
{
  "email": "usuario@ejemplo.com",
  "password": "password123"
}
```
**Response 200**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```
- **401** credenciales inválidas.
- **423** cuenta bloqueada 15 min tras 5 intentos fallidos.
- **429** más de 10 intentos por IP en 15 min.

#### `POST /auth/refresh`
**Request**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```
**Response 200**: nuevo par de tokens. El refresh token usado queda **inválido**; reutilizarlo devuelve **401**.

#### `GET /auth/me`
**Headers**: `Authorization: Bearer <access_token>`
**Response 200**: `UserPublic`

---

### Lotes (`/lots`)

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/lots` | Crear lote con geometría | ✅ |
| GET | `/lots` | Listar lotes (paginado, búsqueda y filtros) | ✅ |
| GET | `/lots/{lot_id}` | Detalle de lote | ✅ |
| GET | `/lots/{lot_id}/versions` | Historial de versiones del lote | ✅ |
| PATCH | `/lots/{lot_id}` | Actualizar nombre y/o geometría | ✅ |
| DELETE | `/lots/{lot_id}` | Eliminar lote (*soft delete*: se conservan los análisis) | ✅ |
| POST | `/lots/{lot_id}/restore` | Restaurar un lote eliminado | ✅ |

#### `POST /lots`
**Headers**: `Authorization: Bearer <access_token>`
**Request** (cuadrado de ~100 ha):
```json
{
  "name": "Lote Norte",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[
      [-59.900, -36.800],
      [-59.900, -36.790],
      [-59.888, -36.790],
      [-59.888, -36.800],
      [-59.900, -36.800]
    ]]
  }
}
```
**Response 201**:
```json
{
  "id": "uuid",
  "name": "Lote Norte",
  "area_ha": 118.81,
  "geometry": { "type": "Polygon", "coordinates": [...] },
  "created_at": "2026-11-11T12:00:00Z",
  "updated_at": "2026-11-11T12:00:00Z",
  "deleted_at": null
}
```
**422** si la geometría no es un Polygon válido, el área está fuera de **0,01 – 10.000 ha** o el usuario ya tiene un lote con ese nombre.

Crear un lote genera la versión 1 en el historial.

#### `GET /lots`
**Query params** (todos opcionales):

| Param | Ejemplo | Descripción |
|-------|---------|-------------|
| `page`, `size` | `1`, `20` | Paginación (size máx 100) |
| `search` | `norte` | Búsqueda por nombre |
| `date_from`, `date_to` | `2026-11-01T00:00:00Z` | Rango de fecha de creación |
| `area_min`, `area_max` | `50`, `500` | Rango de área en ha |
| `bbox` | `-60,-37,-59,-36` | Lotes que intersectan el rectángulo `min_lon,min_lat,max_lon,max_lat` |
| `include_deleted` | `true` | Incluir lotes eliminados |

**Response 200**:
```json
{
  "items": [LotRead, ...],
  "total": 42,
  "page": 1,
  "size": 20
}
```

#### `PATCH /lots/{lot_id}`
**Request** (campos opcionales):
```json
{
  "name": "Nuevo Nombre",
  "geometry": { "type": "Polygon", "coordinates": [...] },
  "change_reason": "Ampliación de límites"
}
```
Si cambia la geometría se crea una nueva versión en el historial; si solo cambia el nombre, no.

---

### Análisis (`/analyses`)

Los recursos forrajeros son mapas de **tasa de crecimiento (kg MS/ha/día)**:

| `resource_type` | Especie | Archivo raster |
|-----------------|---------|----------------|
| `resource_1` | Alfalfa | `alfalfa.tif` |
| `resource_2` | Festuca | `festuca.tif` |
| `resource_3` | Raigrás | `raigras.tif` |
| `resource_4` | Pastizal natural | `pastizal.tif` |

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/analyses` | Iniciar análisis de un lote (asíncrono) | ✅ |
| POST | `/analyses/check-cache` | Ver si ya existe un análisis idéntico | ✅ |
| GET | `/analyses` | Listar análisis del usuario | ✅ |
| GET | `/analyses/{analysis_id}` | Detalle de un análisis | ✅ |
| GET | `/analyses/lots/{lot_id}/analyses` | Análisis de un lote | ✅ |
| GET | `/analyses/timeseries` | Serie temporal por lote y especie | ✅ |
| POST | `/analyses/{analysis_id}/report` | Generar reporte PDF *(experimental, requiere `reportlab`)* | ✅ |

#### `POST /analyses`
**Request**:
```json
{
  "lot_id": "uuid",
  "resource_type": "resource_1",
  "store_clipped_raster": false
}
```
**Response 202**: `AnalysisRead` con `status: "pending"`. El worker de Celery lo procesa y lo pasa a `processing` y después a `completed`, o a `failed` con `error_message`. El frontend consulta `GET /analyses/{id}` cada 3 s hasta que termina.

- Si ya existe un análisis **completado** del mismo lote, especie, geometría y versión de raster, se devuelve ese (cache).
- **409** si ya hay un análisis `pending`/`processing` para el mismo lote y especie:
  ```json
  { "detail": { "error": "Ya existe un análisis en curso para este lote y recurso",
                "existing_analysis_id": "uuid", "existing_status": "pending",
                "retry_after_seconds": 30 } }
  ```
- **404** si el lote no existe o no es del usuario.

**Cálculo**: se recorta el raster al polígono del lote y se promedian los píxeles cuyo centro cae dentro. Si el lote es más chico que un píxel (~11 ha), se toman los píxeles que toca. Se ignoran NoData y valores negativos.

#### `POST /analyses/check-cache`
**Request**: `{ "lot_id": "uuid", "resource_type": "resource_1" }`
**Response 200**: `{ "cached": true|false, "analysis": AnalysisRead|null, "message": "..." }`

#### `GET /analyses`
**Query params**: `lot_id`, `resource_type`, `status` (`pending`/`processing`/`completed`/`failed`), `page`, `size`.

#### `GET /analyses/timeseries`
**Query params**: `lot_id`, `resource_type` (obligatorios).
**Response 200**: `{ "lot_id", "resource_type", "data": [{ "analyzed_at", "average_rate", "resource_type", "raster_version", "raster_date" }] }`

---

### Salud y monitoreo

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Health check (conexión a la BD) |
| GET | `/ready` | Readiness probe (BD + tablas) |
| GET | `/metrics` | Métricas Prometheus |

**Response 200** (`/health`):
```json
{
  "status": "ok",
  "database": "ok",
  "service": "geoforraje-api",
  "version": "1.0.0"
}
```

---

## 📦 Esquemas Principales

### User
```typescript
interface UserPublic {
  id: string;             // UUID
  email: string;
  full_name: string | null;
  created_at: string;     // ISO 8601
  email_verified: boolean;
}
```

### Lot
```typescript
interface LotRead {
  id: string;             // UUID
  name: string;
  area_ha: number;        // Calculado server-side (proyección UTM)
  geometry: GeoJSONPolygon;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

interface LotVersionRead {
  id: string;
  lot_id: string;
  version_number: number; // 1 = creación
  name: string;
  area_ha: number;
  geometry: GeoJSONPolygon;
  changed_by: string;     // UUID del usuario
  change_reason: string | null;
}

interface GeoJSONPolygon {
  type: "Polygon";
  coordinates: number[][][];  // [exterior_ring, interior_ring*], [lon, lat]
}
```

### Analysis
```typescript
interface AnalysisRead {
  id: string;
  lot_id: string;
  resource_type: "resource_1" | "resource_2" | "resource_3" | "resource_4";
  average_rate: number;          // kg MS/ha/día (0 mientras está pending)
  min_value?: number;
  max_value?: number;
  std_dev?: number;
  percentiles?: Record<string, number>;  // p25, p50, p75, p90, p95
  raster_file_reference: string;  // ruta del .tif usado
  raster_version: string;         // ej. "v2026.10.31"
  raster_date: string;            // fecha de los mapas
  clipped_raster_path?: string;
  store_clipped_raster: boolean;
  lot_geometry_hash: string;      // SHA-256 de la geometría (cache)
  analyzed_at: string;
  status: "pending" | "processing" | "completed" | "failed";
  error_message?: string;
}
```

---

## 🔐 Autenticación

- **Tipo**: JWT Bearer Token (HS256), clave en `JWT_SECRET`
- **Access Token**: 15 min de expiración
- **Refresh Token**: 7 días, con rotación (solo vale el último emitido)
- **Header**: `Authorization: Bearer <access_token>`

**Flujo**:
1. `POST /auth/login` → access + refresh
2. Requests con `Authorization: Bearer <access>`
3. Si responde 401, el interceptor del frontend llama a `POST /auth/refresh`
4. `POST /auth/refresh` devuelve un par nuevo e invalida el refresh anterior

---

## ❌ Códigos de Error Comunes

| Código | Significado |
|--------|-------------|
| 400 | Request inválido (email ya registrado, token de verificación inválido) |
| 401 | No autenticado / token expirado o ya usado / credenciales inválidas |
| 403 | Usuario inactivo o eliminado |
| 404 | Recurso no encontrado (lote, análisis) o sin permisos |
| 409 | Análisis en curso para el mismo lote y especie |
| 422 | Error de validación (geometría, área, nombre repetido, parámetros) |
| 423 | Cuenta bloqueada temporalmente |
| 429 | Demasiados intentos de login |
| 500 | Error interno del servidor |

**Formato error**:
```json
{
  "detail": "Mensaje descriptivo del error"
}
```

---

## 📄 OpenAPI Spec

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **JSON Spec**: `http://localhost:8000/openapi.json`
