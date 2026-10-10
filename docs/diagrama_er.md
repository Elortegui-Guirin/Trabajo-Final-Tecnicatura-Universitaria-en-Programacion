# Diagrama Entidad-Relación - GeoForraje 1.0

## Esquema de Base de Datos (PostgreSQL + PostGIS)

```mermaid
erDiagram
    USERS {
        string id PK
        string email UK
        string hashed_password
        string full_name
        boolean is_active
        timestamp last_login
        timestamp created_at
        timestamp updated_at
    }

    LOTS {
        string id PK
        string name
        float area_ha
        geometry geometry (SRID 4326)
        string user_id FK
        timestamp created_at
        timestamp updated_at
    }

    ANALYSES {
        string id PK
        string lot_id FK
        resource_type enum
        float average_rate
        min_value
        max_value
        std_dev
        percentiles jsonb
        string raster_file_reference
        string status
        timestamp analyzed_at
        string error_message
        timestamp created_at
        timestamp updated_at
    }

    USERS ||--o{ LOTS : "crea"
    LOTS ||--o{ ANALYSES : "tiene"
```

## Tablas y Descripción

### 1. `users` (seguridad)
- **Propósito**: Almacena credenciales y datos de usuario autenticado
- **Relacion**: Uno a muchos con lots (un usuario puede tener muchos lotes)
- **Campos clave**: `id` (UUID primary key), `email` (único, para login), `hashed_password`, `is_active`, `last_login`

### 2. `lots` (gestión de lotes)
- **Propósito**: Almacena lotes georreferenciados dibujados sobre el mapa
- **Propiedad**: Cada lote pertenece a un usuario (`user_id` FK)
- **Campos clave**: `id`, `name`, `area_ha` (área calculada automáticamente), `geometry` (GeoJSON/WKB con SRID 4326)
- **Validaciones**: Geometría debe ser polígono válido, orientación CCW (sentido antihorario)

### 3. `analyses` (análisis forrajero)
- **Propósito**: Registra resultados de análisis raster por lote y tipo de recurso
- **Relacion**: Muchos a uno con lots (un lote puede tener múltiples análisis)
- **Campos clave**: `lot_id` FK, `resource_type` (de 1-4 recursos forrajeros), `average_rate` (tasa promedio de crecimiento), `status` (pending/processing/completed/failed)
- **Validaciones**: `average_rate` debe ser número positivo, `status` controla el flujo de trabajo

## Índices y Performance

```sql
-- Índice espacial para consultas geoespaciales
CREATE INDEX idx_lots_geometry ON lots USING GIST (geometry);
-- Índice para queries por usuario
CREATE INDEX idx_lots_user_id ON lots (user_id);
-- Índice para queries de análisis por estado
CREATE INDEX idx_analyses_status ON analyses (status);
-- Índice para búsquedas por tipo de recurso
CREATE INDEX idx_analyses_resource ON analyses (resource_type);
```

## Relaciones Clave

| De | Para | Tipo | Descripción |
|----|------|------|-------------|
| users.id | lots.user_id | 1:N | Un usuario puede tener varios lotes |
| lots.id | analyses.lot_id | 1:N | Un lote puede tener varios análisis |
| users.id | auth tokens (JWT) | 1:1 | Token JWT contiene user_id como sub |