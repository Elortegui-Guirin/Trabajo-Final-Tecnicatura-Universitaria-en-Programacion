# GeoForraje 1.0 - Plataforma de Análisis Forrajero Geoespacial

## Descripción
API y aplicación web para la gestión de lotes agrícolas y análisis de recursos forrajeros mediante procesamiento de imágenes raster (GeoTIFF).

El usuario dibuja sus lotes sobre el mapa y GeoForraje calcula, para cada lote, la **tasa de crecimiento promedio (kg MS/ha/día)** de cuatro especies forrajeras a partir de mapas derivados de MODIS (píxel ≈ 11 ha):

| Especie | Archivo | ID interno |
|---------|---------|------------|
| Alfalfa | `data/rasters/alfalfa.tif` | `resource_1` |
| Festuca | `data/rasters/festuca.tif` | `resource_2` |
| Raigrás | `data/rasters/raigras.tif` | `resource_3` |
| Pastizal natural | `data/rasters/pastizal.tif` | `resource_4` |

Mapas actuales: **31/10/2026**, cobertura provincia de Buenos Aires (EPSG:4326). Ver `data/rasters/LEEME.md`.

---

## Stack Tecnológico

### Backend
- **FastAPI** 0.110+ - API REST moderna y rápida
- **SQLModel** - ORM basado en SQLAlchemy + Pydantic
- **PostgreSQL 15 + PostGIS 3** - Base de datos geoespacial
- **Alembic** - Migraciones de base de datos
- **Python-JOSE + Passlib[bcrypt]** - Autenticación JWT
- **Rasterio + NumPy** - Procesamiento de imágenes geoespaciales
- **Celery + Redis** - Procesamiento de análisis en segundo plano
- **Prometheus FastAPI Instrumentator** - Métricas

### Frontend
- **React 18 + TypeScript** - UI reactiva tipada
- **Vite** - Build tool ultra-rápido
- **Tailwind CSS** - Utility-first CSS
- **TanStack Query v5** - Server state management
- **Zustand** - Client state management
- **React Router v6** - Routing
- **React Hook Form + Zod** - Formularios validados
- **Leaflet + react-leaflet + Geoman** (`@geoman-io/leaflet-geoman-free`) - Mapas interactivos y dibujo de polígonos
- **Recharts** - Gráficos

### DevOps
- **Docker Compose** - Orquestación local
- **Nginx** - Reverse proxy producción
- **GitHub Actions** - CI/CD *(pendiente: todavía no hay workflow en el repo)*

---

## Inicio Rápido

### Prerrequisitos
- **Docker 24+** y **Docker Compose 2+**
- (Opcional) Python 3.11+, Node.js 20+ para desarrollo local sin Docker
- Git

### Paso a paso con Docker (Recomendado)

```bash
# 1. Clonar repositorio
git clone https://github.com/Elortegui-Guirin/Trabajo-Final-Tecnicatura-Universitaria-en-Programacion.git
cd Trabajo-Final-Tecnicatura-Universitaria-en-Programacion

# 2. Levantar todos los servicios
#    (backend, worker de Celery, frontend, postgres+postgis, redis, pgadmin)
make up            # o: docker compose up -d --build

# 3. Verificar que todo funciona
curl http://localhost:8000/health
# Debería mostrar: {"status":"ok","database":"ok",...}
docker compose ps  # todos los servicios en "running"/"healthy"

# 4. Las tablas se crean solas al iniciar el backend (AUTO_CREATE_TABLES=true).
#    NO correr `make migrate` por ahora: las migraciones de Alembic quedaron
#    desactualizadas respecto de los modelos y hay que regenerarlas.

# 5. Para probar los análisis: copiar los GeoTIFF en data/rasters/
#    Los mapas ya vienen en el repo: data/rasters/{alfalfa,festuca,raigras,pastizal}.tif
```

### Accesos una vez levantado

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| **Frontend** | http://localhost:5173 | - |
| **Backend API** | http://localhost:8000 | - |
| **Swagger Docs** | http://localhost:8000/docs | - |
| **Health Check** | http://localhost:8000/health | - |
| **pgAdmin** | http://localhost:5050 | admin@geoforraje.com / admin |
| **Postgres** | localhost:5432 | postgres / postgres / geoforraje |

### Primer uso

1. Abre **http://localhost:5173**
2. Click **"Regístrate"** → completa email, nombre, contraseña (mín 8 chars)
3. Inicia sesión automáticamente → redirige a **Dashboard**
4. Ve a **"Mis Lotes"** → **"Nuevo Lote"**
5. Dibuja un polígono en el mapa → ponle nombre → **"Crear lote"**
6. El lote aparece en la lista con su área calculada en hectáreas
7. Entra al lote → **"Ver historial de análisis"** → **"Analizar Alfalfa"** (o festuca, raigrás, pastizal)
8. El análisis se procesa en segundo plano (worker de Celery) y en unos segundos pasa a **Completado** con la tasa promedio, mínimo, máximo y percentiles

> **Lote de ejemplo para probar**: dibujar un rectángulo cerca de Azul, entre longitud −59,900 y −59,888 y latitud −36,800 y −36,790 (~120 ha). Resultado esperado: alfalfa ≈ 12,6 · festuca ≈ 12,6 · raigrás ≈ 17,6 · pastizal ≈ 9,7 kg MS/ha/día.
>
> El lote tiene que estar dentro de la provincia de Buenos Aires y fuera de zonas urbanas o agua (sin dato en los mapas).

---

## Comandos Útiles (Makefile)

```bash
make help           # Ver todos los comandos disponibles
make up             # Levantar todo (docker compose up -d --build)
make down           # Bajar servicios y volúmenes
make logs           # Ver logs de todos los servicios
docker compose logs -f celery-worker   # Logs del worker de análisis

# Backend
make backend-shell  # Shell en contenedor backend
make backend-lint   # ruff + mypy
make backend-fmt    # ruff format
make backend-test   # pytest con coverage

# Frontend
make frontend-shell # Shell en contenedor frontend
make frontend-lint  # eslint + prettier check
make frontend-fmt   # prettier --write
make frontend-test  # vitest (todavía no hay tests de frontend)
make frontend-typecheck # tsc --noEmit

# Base de Datos
make migrate        # Aplicar migraciones (alembic upgrade head)
make migrate-create MSG="descripción"  # Nueva migración
make migrate-history # Ver historial
make db-shell       # psql en contenedor postgres

# Calidad
make lint           # Lint backend + frontend
make fmt            # Formatear todo
make test           # Tests backend + frontend
make verify-phase1  # Verificación completa Fase 1

# Generación
make gen-types      # Generar tipos TS desde OpenAPI
make ci-build       # Build imágenes producción

# Limpieza
make clean          # Limpiar contenedores, volúmenes, cache
make clean-all      # Limpieza agresiva (incluye node_modules, __pycache__)
```

---

## Estructura del Proyecto

```
geoforraje/
├── backend/
│   ├── app/
│   │   ├── api/           # Dependencias FastAPI (deps, security)
│   │   ├── core/          # Config, security (JWT, bcrypt), raster_config (catálogo de mapas)
│   │   ├── db/            # Database engine, session, init
│   │   ├── models/        # SQLModel: User, Lot, LotVersion, Analysis, AuditLog
│   │   ├── routers/       # Endpoints: auth, lots, analyses, health
│   │   ├── schemas/       # Pydantic: request/response models
│   │   ├── services/      # Lógica: lot_service, raster_service, notification_service (simulado)
│   │   ├── workers/       # Celery: análisis raster + tareas periódicas
│   │   └── utils/         # Generador de reportes PDF
│   ├── alembic/           # Migraciones (desactualizadas, ver más abajo)
│   ├── tests/             # pytest (auth, lots, raster, health)
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/    # Shared: Layout, MapView/MapEditor (react-leaflet + Geoman)
│   │   ├── pages/         # DashboardPage
│   │   ├── modules/       # Feature modules
│   │   │   ├── auth/      # Login, Register, store, api
│   │   │   ├── lots/      # List, Form, Detail
│   │   │   └── results/   # Análisis: historial, detalle, gráfico
│   │   ├── hooks/         # useGeoJSON
│   │   ├── types/         # Tipos TS (api.ts, analysis.ts con nombres de especies)
│   │   └── styles/        # globals.css (Tailwind + components)
│   ├── Dockerfile
│   └── package.json
├── data/
│   └── rasters/           # Mapas GeoTIFF de tasa de crecimiento (4 especies)
├── docs/                  # Documentación del sistema
│   ├── requerimientos.md  # FR/NFR + estado de implementación
│   ├── negocio.md         # Reglas de negocio (fuente única, con IDs RN-…)
│   ├── trazabilidad.md    # Matriz requerimiento ↔ regla ↔ API ↔ tabla ↔ módulo ↔ test
│   ├── analisis_y_diseno.md # Casos de uso, actividades, estados y clases
│   ├── arquitectura.md    # Componentes, flujos, despliegue y decisiones
│   ├── diagrama_er.md     # Diagrama Entidad-Relación
│   ├── API_SPECS.md       # Endpoints, esquemas y errores
│   ├── CHANGELOG.md       # Registro de cambios
│   └── CONTRIBUTING.md    # Guía de contribución
├── docker-compose.yml     # Desarrollo
├── docker-compose.prod.yml # Producción
├── Makefile               # ~30 comandos (make help)
└── README.md
```

---

## Fases de Desarrollo

| Fase | Descripción | Estado |
|------|-------------|--------|
| 1 | Repositorio, README, modelo de datos, Docker, CI | 🟡 Completada salvo CI (no hay GitHub Actions) |
| 2 | Autenticación JWT (register, login, refresh con rotación, me) | ✅ Completada |
| 3 | CRUD Lotes + validación geometría + ownership + versiones | ✅ Completada |
| 4 | Mapa Leaflet + Geoman (dibujar, editar, capas base OSM/satélite) | ✅ Completada (reescrita el 11/11, ver CHANGELOG) |
| 5 | Análisis raster (GeoTIFF, Rasterio, Celery) + despliegue prod | 🟡 Análisis implementado con mapas reales; despliegue prod sin probar |

El estado de cada requerimiento está en `docs/requerimientos.md` y los cambios en `docs/CHANGELOG.md`. La especificación original por fase (`docs/fase_*.md`) se retiró el 18/11 porque describía decisiones que luego cambiaron; queda disponible en el historial de git.

### Pendientes conocidos
- Regenerar las migraciones de Alembic para que coincidan con los modelos.
- Workflow de CI (GitHub Actions) con lint + tests.
- Tests de frontend (vitest) y correr `make frontend-typecheck`.
- Export/Import de lotes en GeoJSON (FR-08, prioridad baja).
- Serie temporal: cargar mapas de varias fechas por especie (la base ya guarda versión y fecha del raster en cada análisis).

---

## Features a futuro

> **Nota:** los siguientes ítems son **ideas registradas**, no compromisos de entrega. Amplían el backlog del proyecto y **no** forman parte del alcance de la versión 1.0. (Los pendientes técnicos inmediatos están en "Pendientes conocidos".)

| Feature | Descripción |
|---------|-------------|
| **Notificaciones por email reales** | Los endpoints de verificación de email y reseteo de contraseña funcionan, pero el envío real está simulado (solo registra en logs). Requiere integrar un proveedor (SendGrid, Mailgun, SES). |
| **Alertas push y multi-canal** | Existe la base de un servicio de notificaciones (email/push/webhook) sin conectar a proveedores reales. Permitiría avisar al usuario cuando un análisis termina o se detecta una anomalía de crecimiento. |
| **Integración con fuentes satelitales (Google Earth Engine / Sentinel)** | La tarea programada de actualización de mapas es un placeholder. Permitiría descargar y actualizar los GeoTIFF automáticamente desde imágenes satelitales, sin reemplazo manual. |
| **Export / Import de lotes (GeoJSON)** | Requerimiento FR-08 de prioridad baja: descargar lotes como archivo GeoJSON o importar geometrías existentes desde archivos. |
| **Trazabilidad activa de cambios (AuditLog)** | La tabla y el modelo `AuditLog` existen en la BD, pero el registro de quién modificó qué y cuándo queda como evolución futura (no está activo en el MVP). |
| **Reporte PDF del análisis** | Existe un generador de reportes (logo, metadata, estadísticas, leyenda) en estado de prototipo: todavía no está integrado ni probado, y le falta incrustar el mapa del lote. |
| **Actualización en tiempo real (WebSockets)** | Hoy el estado de los análisis se consulta por polling. WebSockets actualizaría la UI sin necesidad de refrescos manuales. |
| **Series temporales multi-fecha y comparación de campañas** | El endpoint y el gráfico de serie temporal por lote y especie existen, pero con mapas de una sola fecha (31/10/2026) muestran un único punto; se prevé cargar mapas de varias fechas y comparar campañas o periodos. |
| **App mobile** | Cliente móvil (React Native / Flutter) para consultar lotes y análisis en el campo sin necesidad de navegador. |
| **API pública** | Exponer los endpoints con documentación y claves de acceso para que sistemas de terceros consuman el servicio. |
| **Multi-tenant (organizaciones)** | La arquitectura está preparada (NFR-14), pero el modelo actual es single-user. Permitiría agrupar usuarios y lotes por organización. |
| **Escalabilidad: microservicios y caching layer** | Separar análisis y mapa en servicios independientes, y cachear tokens/sesiones en Redis (hoy Redis se usa solo como broker de Celery). |

---

## Documentación Adicional

| Archivo | Descripción |
|---------|-------------|
| `docs/requerimientos.md` | Requerimientos Funcionales (FR) y No Funcionales (NFR), con estado de implementación |
| `docs/negocio.md` | Reglas de negocio con identificador (RN-GEO, RN-AUTH, RN-LOT, RN-ANA, RN-MAP, RN-AUD) |
| `docs/trazabilidad.md` | Matriz de trazabilidad: requerimientos ↔ reglas ↔ API ↔ tablas ↔ módulos ↔ tests |
| `docs/analisis_y_diseno.md` | Casos de uso, diagramas de actividades, de estados y de clases |
| `docs/arquitectura.md` | Componentes, flujo de análisis, autenticación, despliegue y decisiones |
| `docs/diagrama_er.md` | Diagrama Entidad-Relación (Mermaid) |
| `docs/API_SPECS.md` | Endpoints, esquemas, códigos error, autenticación |
| `docs/CONTRIBUTING.md` | Guía de contribución, ramas, commits, PRs, testing |
| `docs/CHANGELOG.md` | Registro de cambios y pendientes |
| `data/rasters/LEEME.md` | Mapas de tasa de crecimiento: archivos, especies, fecha |

---

## Variables de Entorno

### Backend (`.env` en `backend/`)
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/geoforraje
JWT_SECRET=tu-clave-secreta-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=["http://localhost:5173"]
RASTER_DATA_PATH=/data/rasters
REDIS_URL=redis://redis:6379/0
AUTO_CREATE_TABLES=true   # crea las tablas al iniciar (desarrollo)
LOG_LEVEL=INFO
```

En desarrollo no hace falta crear `.env`: `docker-compose.yml` ya define estas variables.

### Frontend (`.env` en `frontend/`)
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=GeoForraje 1.0
```

**Copiar desde `.env.example` y ajustar**.

---

## Testing

```bash
# Backend (pytest + coverage)
make backend-test

# Frontend (vitest)
make frontend-test

# Todo
make test
```

Los tests del backend usan una base de datos aparte (`geoforraje_test`), que se crea sola y se vacía antes de cada test. Celery se simula: los análisis quedan en `pending` y no se procesan rasters.

Para correrlos con el entorno levantado: `docker compose exec backend pytest -v`

**Coverage objetivo**: 80%

---

## Linting & Formatting

```bash
make lint        # ruff + mypy (backend) + eslint + prettier (frontend)
make fmt         # ruff format + prettier --write
```

---

## Migraciones (Alembic)

> ⚠️ **Desactualizadas.** Las migraciones de `backend/alembic/versions/` no coinciden con los modelos actuales. Por ahora las tablas las crea el backend al iniciar (`AUTO_CREATE_TABLES=true`). Antes de producción hay que regenerarlas (`make migrate-create`) y poner `AUTO_CREATE_TABLES=false`.

```bash
make migrate              # Aplicar pendientes
make migrate-create MSG="add user fields"  # Nueva migración
make migrate-history      # Ver historial
make migrate-downgrade    # Revertir última
make db-shell             # psql directo
```

---

## Despliegue Producción

```bash
# Build imágenes producción
make ci-build

# Deploy con docker-compose.prod.yml
docker compose -f docker-compose.prod.yml up -d

# Incluye:
# - Nginx reverse proxy con SSL (Let's Encrypt)
# - Backend: Gunicorn + Uvicorn workers
# - Frontend: Nginx estático
# - PostgreSQL + PostGIS
# - Redis + worker y beat de Celery (análisis raster)
# - Prometheus + Grafana (monitoreo)
```

---

## Uso de IA

Durante el desarrollo se utilizaron dos herramientas de IA como apoyo: **OpenCode con MiMoCode** (en la construcción inicial) y **Claude** (Anthropic, en la etapa de corrección, puesta en marcha y documentación).

1. **Codificación de la interfaz de usuario (frontend React + Leaflet)**
   Se usó para generar los componentes base de la UI (formularios, listas, mapa interactivo con dibujo de polígonos) porque el tiempo de entrega era acotado y se necesitaba acelerar esa parte del trabajo.
   **Ventaja observada:** reducción significativa del tiempo de maquetación y generación de borradores funcionales, lo que permitió enfocar el esfuerzo del equipo en la lógica de negocio y las reglas de validación.

2. **Brecha de conocimiento en tecnologías geoespaciales y de procesamiento (PostGIS, Rasterio, Celery)**
   Se usó para entender e implementar el procesamiento de imágenes raster, el recorte por geometría del lote y la ejecución de tareas en background, porque el equipo no tenía experiencia previa con esas tecnologías.
   **Ventaja observada:** la herramienta sirvió como apoyo para comprender el enfoque técnico y generar un primer borrador funcional sin bloquear el avance del proyecto, acortando la curva de aprendizaje.

3. **Revisión, depuración y puesta en marcha del sistema (Claude)**
   Se usó Claude para revisar el estado del proyecto y corregir los errores que impedían arrancarlo: errores de sintaxis, modelos duplicados, rutas mal definidas, incompatibilidades de dependencias y el módulo de mapas. También se usó para ejecutarlo con Docker en Windows e integrar los mapas GeoTIFF de tasa de crecimiento de las cuatro especies.
   **Ventaja observada:** se pasó de un código que no arrancaba a un sistema funcional de punta a punta (registro, lotes, análisis raster y dashboard) en pocos días. Cada corrección quedó registrada en `docs/CHANGELOG.md`.

4. **Documentación y respuesta a la revisión del tutor (Claude)**
   Se usó para unificar las reglas de negocio, renumerar los requerimientos y elaborar la matriz de trazabilidad y los diagramas de análisis y diseño (casos de uso, actividades, estados y clases), contrastándolos con el código real.
   **Ventaja observada:** la documentación quedó consistente con lo implementado y se eliminaron los documentos obsoletos que se contradecían entre sí.

En todos los casos, el equipo revisó, probó y validó el código y la documentación generados antes de incorporarlos al repositorio.

---

## Licencia
Proyecto académico - Tecnicatura Universitaria en Programación - Programación IV - 2026

**Integrantes**:
- Verónica Guirin
- María del Rosario Margarita Iturralde Elortegui

**Tutor**: Gerardo Adrián Herrera
