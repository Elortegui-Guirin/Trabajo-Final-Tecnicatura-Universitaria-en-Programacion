# GeoForraje 1.0 - Plataforma de Análisis Forrajero Geoespacial

## Descripción
API y aplicación web para la gestión de lotes agrícolas y análisis de recursos forrajeros mediante procesamiento de imágenes raster (GeoTIFF).

---

## Stack Tecnológico

### Backend
- **FastAPI** 0.110+ - API REST moderna y rápida
- **SQLModel** - ORM basado en SQLAlchemy + Pydantic
- **PostgreSQL 15 + PostGIS 3** - Base de datos geoespacial
- **Alembic** - Migraciones de base de datos
- **Python-JOSE + Passlib[bcrypt]** - Autenticación JWT
- **Rasterio + NumPy** - Procesamiento de imágenes geoespaciales
- **Prometheus FastAPI Instrumentator** - Métricas

### Frontend
- **React 18 + TypeScript** - UI reactiva tipada
- **Vite** - Build tool ultra-rápido
- **Tailwind CSS** - Utility-first CSS
- **TanStack Query v5** - Server state management
- **Zustand** - Client state management
- **React Router v6** - Routing
- **React Hook Form + Zod** - Formularios validados
- **Leaflet + react-leaflet + leaflet.pm** - Mapas interactivos
- **Recharts** - Gráficos

### DevOps
- **Docker Compose** - Orquestación local
- **Nginx** - Reverse proxy producción
- **GitHub Actions** - CI/CD

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
#    (backend, frontend, postgres+postgis, pgadmin)
make up

# 3. Verificar que todo funciona
make health
# Debería mostrar:
# === Backend ===  {"status":"ok","database":"ok",...}
# === Frontend === 200 OK
# === Postgres === accepting connections
# === PgAdmin === 200 OK

# 4. (Opcional) Aplicar migraciones si es la primera vez
make migrate
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

---

## Comandos Útiles (Makefile)

```bash
make help           # Ver todos los comandos disponibles
make up             # Levantar todo (docker compose up -d --build)
make down           # Bajar servicios y volúmenes
make logs           # Ver logs de todos los servicios
make health         # Health check de todos los servicios

# Backend
make backend-shell  # Shell en contenedor backend
make backend-lint   # ruff + mypy
make backend-fmt    # ruff format
make backend-test   # pytest con coverage

# Frontend
make frontend-shell # Shell en contenedor frontend
make frontend-lint  # eslint + prettier check
make frontend-fmt   # prettier --write
make frontend-test  # vitest
make frontend-typecheck # tsc --noEmit

# Base de Datos
make migrate        # Aplicar migraciones (alembic upgrade head)
make migrate-create MSG="descripción"  # Nueva migración
make migrate-history # Ver historial
make migrate-downgrade # Revertir última
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
│   │   ├── core/          # Config, security (JWT, bcrypt)
│   │   ├── db/            # Database engine, session, init
│   │   ├── models/        # SQLModel: User, Lot, Analysis
│   │   ├── routers/       # Endpoints: auth, lots, health
│   │   ├── schemas/       # Pydantic: request/response models
│   │   ├── services/      # Lógica: lot_service, geometry_service
│   │   ├── workers/       # Background tasks (Fase 5)
│   │   └── utils/         # Utilidades
│   ├── alembic/           # Migraciones (versions/)
│   ├── tests/             # pytest (auth, lots, health)
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/    # Shared: Layout, MapView/*
│   │   ├── pages/         # DashboardPage
│   │   ├── modules/       # Feature modules
│   │   │   ├── auth/      # Login, Register, store, api
│   │   │   ├── lots/      # List, Form, Detail, MapEditor
│   │   │   ├── map/       # (Fase 4 componentes)
│   │   │   └── results/   # (Fase 5)
│   │   ├── hooks/         # useAuth, useLots, useGeoJSON, useMap
│   │   ├── types/         # TypeScript types (api.ts)
│   │   └── styles/        # globals.css (Tailwind + components)
│   ├── Dockerfile
│   └── package.json
├── shared/
│   └── schemas/           # Contratos compartidos (generados)
├── spec/
│   └── printable/         # Spec por fase (5 archivos + README)
├── docs/                  # Documentación adicional
│   ├── diagrama_er.md     # ER Diagram (Mermaid)
│   ├── arquitectura.md    # Arquitectura C4 + secuencia + despliegue
│   ├── requerimientos.md  # FR/NFR formales
│   ├── negocio.md         # Reglas de negocio
│   ├── API_SPECS.md       # Documentación endpoints
│   └── CONTRIBUTING.md    # Guía contribución
├── docker-compose.yml     # Desarrollo
├── docker-compose.prod.yml # Producción
├── Makefile               # 40+ comandos
└── README.md
```

---

## Fases de Desarrollo

| Fase | Descripción | Estado |
|------|-------------|--------|
| 1 | Repositorio, README, modelo de datos, Docker, CI | ✅ Completada |
| 2 | Autenticación JWT (register, login, refresh, me) | ✅ Completada |
| 3 | CRUD Lotes + validación geometría + ownership | ✅ Completada |
| 4 | Mapa Leaflet + leaflet.pm (dibujar, editar, capas base, popups) | ✅ Completada |
| 5 | Análisis raster (GeoTIFF, Rasterio) + despliegue prod | ⏳ Pendiente |

Ver `spec/printable/` para especificación detallada por fase.

---

## Documentación Adicional

| Archivo | Descripción |
|---------|-------------|
| `docs/diagrama_er.md` | Diagrama Entidad-Relación (Mermaid) |
| `docs/arquitectura.md` | Arquitectura C4, secuencia, despliegue, decisiones |
| `docs/requerimientos.md` | Requerimientos Funcionales (FR) y No Funcionales (NFR) |
| `docs/negocio.md` | Reglas de negocio (validación geometría, auth, lotes, análisis) |
| `docs/API_SPECS.md` | Endpoints, esquemas, códigos error, autenticación |
| `docs/CONTRIBUTING.md` | Guía de contribución, ramas, commits, PRs, testing |

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
LOG_LEVEL=INFO
```

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

**Coverage mínimo**: 80%

---

## Linting & Formatting

```bash
make lint        # ruff + mypy (backend) + eslint + prettier (frontend)
make fmt         # ruff format + prettier --write
```

---

## Migraciones (Alembic)

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
# - Redis (para Celery en Fase 5)
# - Prometheus + Grafana (monitoreo)
```

---

## Licencia
Proyecto académico - Tecnicatura Universitaria en Programación - Programación IV - 2026

**Integrantes**:
- Verónica Guirin
- María del Rosario Margarita Iturralde Elortegui

**Tutor**: Gerardo Adrián Herrera