# Arquitectura del Sistema - GeoForraje 1.0

GeoForraje es una aplicación web cliente-servidor. El frontend (React) permite dibujar lotes sobre un mapa; la API (FastAPI) valida y guarda las geometrías en PostgreSQL/PostGIS; y un worker (Celery) recorta los mapas de crecimiento de pasturas al polígono de cada lote para calcular su tasa promedio.

## 1. Componentes

```mermaid
flowchart LR
    U(["Usuario<br/>navegador"])

    subgraph FE["Frontend · React + TypeScript + Vite"]
        direction TB
        PAGES["Páginas<br/>Dashboard · Lotes · Análisis · Auth"]
        MAP["MapEditor<br/>Leaflet + Geoman"]
        STATE["Estado<br/>Zustand (sesión) · TanStack Query (datos)"]
    end

    subgraph BE["API · FastAPI + SQLModel"]
        direction TB
        ROUTERS["Routers<br/>/auth · /lots · /analyses · /health"]
        SERVICES["Servicios<br/>lot_service · raster_service"]
        SEC["Seguridad<br/>JWT · bcrypt"]
    end

    subgraph WK["Worker · Celery"]
        TASK["run_analysis_task<br/>Rasterio + NumPy"]
    end

    DB[("PostgreSQL 15<br/>+ PostGIS")]
    REDIS[("Redis<br/>cola de tareas")]
    TIF[/"Mapas GeoTIFF<br/>data/rasters/*.tif"/]

    U --> PAGES
    PAGES --- MAP
    PAGES --- STATE
    STATE -- "HTTP/JSON + Bearer JWT" --> ROUTERS
    ROUTERS --> SEC
    ROUTERS --> SERVICES
    SERVICES -- "SQL + geometrías" --> DB
    ROUTERS -- "encola análisis" --> REDIS
    REDIS --> TASK
    TASK -- "lee" --> TIF
    TASK -- "guarda resultado" --> DB
```

| Componente | Responsabilidad |
|------------|-----------------|
| **Frontend** | Interfaz: registro e inicio de sesión, dibujo y gestión de lotes, pedido y visualización de análisis, panel de control |
| **API** | Reglas de negocio, validación de geometrías, autenticación y autorización, persistencia; encola los análisis |
| **Worker Celery** | Procesa cada análisis fuera del request: recorta el raster al lote y calcula las estadísticas |
| **PostgreSQL + PostGIS** | Guarda usuarios, lotes (con su polígono), versiones y análisis; índice espacial para filtrar por zona |
| **Redis** | Cola de mensajes entre la API y el worker |
| **Mapas GeoTIFF** | Tasa de crecimiento (kg MS/ha/día) de 4 especies, derivados de MODIS (píxel ≈ 11 ha), 31/10/2026 |

## 2. Flujo principal: crear un lote y analizarlo

```mermaid
sequenceDiagram
    actor U as Usuario
    participant FE as Frontend
    participant API as API FastAPI
    participant DB as PostgreSQL/PostGIS
    participant Q as Redis
    participant W as Worker Celery

    U->>FE: Dibuja el polígono y pone un nombre
    FE->>FE: Valida forma y área aproximada (useGeoJSON)
    FE->>API: POST /lots {name, geometry}
    API->>API: Valida polígono, calcula área en UTM, nombre único
    API->>DB: INSERT lots + lot_versions (v1)
    API-->>FE: 201 LotRead (área oficial)

    U->>FE: Elige "Analizar Alfalfa"
    FE->>API: POST /analyses {lot_id, resource_type}
    API->>DB: ¿Hay cache? ¿Hay uno en curso?
    alt Ya existe el mismo análisis
        API-->>FE: 202 análisis existente (completed)
    else Hay uno en curso
        API-->>FE: 409 Conflict
    else Nuevo
        API->>DB: INSERT analyses (pending)
        API->>Q: encola run_analysis_task(id)
        API-->>FE: 202 AnalysisRead (pending)
        Q->>W: entrega la tarea
        W->>DB: status = processing
        W->>W: Recorta alfalfa.tif al lote y calcula estadísticas
        W->>DB: status = completed + resultados
    end
    loop cada 2 s mientras esté pending/processing
        FE->>API: GET /analyses/{id}
        API-->>FE: estado actual
    end
    FE-->>U: Tasa promedio en kg MS/ha/día
```

## 3. Autenticación: login, rotación y logout

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant API as API
    participant DB as users

    FE->>API: POST /auth/login {email, password}
    API->>DB: verifica contraseña (bcrypt), guarda refresh_token_jti = J1
    API-->>FE: access (15 min) + refresh (7 días, jti = J1)

    Note over FE,API: Requests con Authorization: Bearer access

    FE->>API: GET /lots → 401 (access vencido)
    FE->>API: POST /auth/refresh {refresh J1}
    API->>DB: ¿jti guardado == J1? sí → guarda J2
    API-->>FE: access nuevo + refresh (jti = J2)
    FE->>API: reintenta GET /lots → 200

    FE->>API: POST /auth/refresh {refresh J1} (reutilizado)
    API-->>FE: 401 (J1 ya no es el vigente)

    FE->>API: POST /auth/logout (Bearer access)
    API->>DB: refresh_token_jti = NULL
    API-->>FE: 200
    FE->>FE: borra tokens y redirige a /login
```

El refresh token se invalida en el servidor guardando solo el identificador (`jti`) del vigente en `users.refresh_token_jti`. No se guarda el token en sí. Ver reglas RN-AUTH-03 a RN-AUTH-06 en [`negocio.md`](negocio.md).

## 4. Despliegue

### Desarrollo (`docker compose up -d --build`)

```mermaid
flowchart LR
    FE["frontend<br/>Vite :5173"] -- API --> BE["backend<br/>uvicorn :8000"]
    BE --> PG[("postgres<br/>PostGIS :5432")]
    BE --> RD[("redis :6379")]
    RD --> WK["celery-worker"]
    WK --> PG
    PGA["pgadmin :5050"] --> PG
    TIF[/"./data/rasters"/] -.volumen.-> BE
    TIF -.volumen.-> WK
```

### Producción (`docker-compose.prod.yml`)

Nginx sirve el frontend compilado y hace de proxy hacia la API (Gunicorn + Uvicorn workers), con PostgreSQL/PostGIS, Redis, worker y beat de Celery, Prometheus y Grafana. Todavía no se desplegó en un servidor público.

## 5. Decisiones de arquitectura

| Decisión | Por qué |
|----------|---------|
| **FastAPI + SQLModel** | API asíncrona, validación con Pydantic y documentación Swagger automática; SQLModel une modelos de BD y esquemas |
| **PostgreSQL + PostGIS** | Estándar para datos geoespaciales: tipo `geometry`, índices espaciales y funciones como intersección por bounding box |
| **Shapely + pyproj** | Validar polígonos y calcular el área real proyectando a la zona UTM del lote |
| **Rasterio + NumPy** | Recortar un GeoTIFF por polígono y calcular estadísticas sin cargar el mapa entero |
| **Celery + Redis** | El análisis no bloquea la API; permite control de concurrencia y reintentos |
| **JWT con rotación de refresh token** | Sesión sin estado para el access token; el `jti` guardado permite invalidar el refresh token (rotación y logout) |
| **Eliminación lógica** | Conserva el historial de lotes y análisis y permite restaurar |
| **React + Vite + TanStack Query** | Interfaz rápida de desarrollar; TanStack Query maneja cache y *polling* del estado de los análisis |
| **Leaflet + Geoman** | Mapas sin costo de licencia; Geoman da herramientas de dibujo y edición de polígonos |
| **Mapas MODIS por especie** | Cobertura provincial de tasa de crecimiento ya procesada; un archivo por especie |
| **Docker Compose** | El mismo entorno en todas las máquinas del equipo |

## 6. Limitaciones conocidas

- Los mapas son de una sola fecha (31/10/2026); la serie temporal crecerá cuando se carguen mapas de otras fechas.
- Los emails de verificación y recuperación se registran en el log, no se envían.
- El límite de intentos de login por IP se guarda en memoria: se reinicia con el backend y no se comparte entre instancias.
- Las migraciones de Alembic están desactualizadas; en desarrollo las tablas se crean desde los modelos.
