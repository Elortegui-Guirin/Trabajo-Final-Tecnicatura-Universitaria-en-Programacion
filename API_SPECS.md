# Documentación de API - GeoForraje 1.0

Basado en OpenAPI/Swagger (`GET /openapi.json`). Generado desde código FastAPI.

---

## 🔗 Endpoints por Módulo

### Autenticación (`/auth`)

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register` | Registrar nuevo usuario | ❌ |
| POST | `/auth/login` | Login, retorna access + refresh tokens | ❌ |
| POST | `/auth/refresh` | Rotar refresh token, nuevo par | ❌ |
| GET | `/auth/me` | Usuario actual desde token | ✅ |
| POST | `/auth/logout` | Logout (limpia store frontend) | ✅ |

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
  "id": "uuid",
  "email": "usuario@ejemplo.com",
  "full_name": "Juan Pérez",
  "created_at": "2026-09-10T12:00:00Z"
}
```

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

#### `POST /auth/refresh`
**Request**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```
**Response 200**: Nuevo par de tokens (el anterior se invalida)

#### `GET /auth/me`
**Headers**: `Authorization: Bearer <access_token>`
**Response 200**: `UserPublic` (sin password)

---

### Lotes (`/lots`)

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/lots` | Crear lote con geometría | ✅ |
| GET | `/lots` | Listar lotes (paginado, búsqueda) | ✅ |
| GET | `/lots/{lot_id}` | Detalle de lote | ✅ |
| PATCH | `/lots/{lot_id}` | Actualizar nombre y/o geometría | ✅ |
| DELETE | `/lots/{lot_id}` | Eliminar lote (cascada analyses) | ✅ |

#### `POST /lots`
**Headers**: `Authorization: Bearer <access_token>`
**Request**:
```json
{
  "name": "Lote Norte",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[
      [-58.5, -34.5],
      [-58.5, -34.4],
      [-58.4, -34.4],
      [-58.4, -34.5],
      [-58.5, -34.5]
    ]]
  }
}
```
**Response 201**:
```json
{
  "id": "uuid",
  "name": "Lote Norte",
  "area_ha": 102.45,
  "geometry": { "type": "Polygon", "coordinates": [...] },
  "created_at": "2026-09-10T12:00:00Z",
  "updated_at": "2026-09-10T12:00:00Z"
}
```

#### `GET /lots`
**Query params**: `page=1`, `size=20`, `search=texto`
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
  "geometry": { "type": "Polygon", "coordinates": [...] }
}
```

---

### Salud (`/health`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Health check (DB connection) |
| GET | `/ready` | Readiness probe (DB + tablas) |

**Response 200**:
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
  id: string;           // UUID
  email: string;
  full_name: string;
  created_at: string;   // ISO 8601
}
```

### Lot
```typescript
interface LotRead {
  id: string;           // UUID
  name: string;
  area_ha: number;      // Calculado server-side
  geometry: GeoJSONPolygon;
  created_at: string;
  updated_at: string;
}

interface GeoJSONPolygon {
  type: "Polygon";
  coordinates: number[][][];  // [exterior_ring, interior_ring*]
}
```

### Analysis
```typescript
interface AnalysisRead {
  id: string;
  lot_id: string;
  resource_type: "resource_1" | "resource_2" | "resource_3" | "resource_4";
  average_rate: number;
  min_value?: number;
  max_value?: number;
  std_dev?: number;
  percentiles?: Record<string, number>;  // p25, p50, p75
  raster_file_reference: string;
  analyzed_at: string;
  status: "pending" | "processing" | "completed" | "failed";
  error_message?: string;
}
```

---

## 🔐 Autenticación

- **Tipo**: JWT Bearer Token (HS256)
- **Access Token**: 15 min expiración
- **Refresh Token**: 7 días, rotación automática
- **Header**: `Authorization: Bearer <access_token>`

**Flujo**:
1. `POST /auth/login` → access + refresh
2. Requests con `Authorization: Bearer <access>`
3. 401 → auto-refresh via interceptor frontend
4. `POST /auth/refresh` rota refresh token

---

## ❌ Códigos de Error Comunes

| Código | Significado |
|--------|-------------|
| 400 | Request inválido (validación Pydantic) |
| 401 | No autenticado / token expirado / credenciales inválidas |
| 403 | Usuario inactivo / sin permisos |
| 404 | Recurso no encontrado (lote, analysis) |
| 422 | Error de validación (geometría inválida, etc.) |
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

**Generar tipos TypeScript**:
```bash
make gen-types
# Genera frontend/src/types/api.ts desde openapi.json
```

---

## 📚 Versionado

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0.0 | 2026-09 | Fases 1-4 completadas |

---

*Generado automáticamente desde código FastAPI. Para cambios, editar routers/schemas y regenerar.*