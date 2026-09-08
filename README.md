# README.md - GeoForraje 1.0
# GeoForraje 1.0 - Plataforma de Análisis Forrajero Geoespacial

## Descripción
API y aplicación web para la gestión de lotes agrícolas y análisis de recursos forrajeros mediante procesamiento de imágenes raster (GeoTIFF).

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

## Inicio Rápido

### Prerrequisitos
- Docker 24+ y Docker Compose 2+
- (Opcional) Python 3.11+, Node.js 20+ para desarrollo local sin Docker

### Con Docker (Recomendado)
```bash
# Clonar y entrar
git clone <repo> geoforraje
cd geoforraje

# Levantar todo (backend, frontend, postgres+postgis, pgadmin)
make up

# Verificar
make health
# Debería mostrar todos los servicios OK
```

### Accesos
| Servicio | URL | Credenciales |
|----------|-----|--------------|
| Frontend | http://localhost:5173 | - |
| Backend API | http://localhost:8000 | - |
| Swagger Docs | http://localhost:8000/docs | - |
| Health Check | http://localhost:8000/health | - |
| pgAdmin | http://localhost:5050 | admin@geoforraje.com / admin |
| Postgres | localhost:5432 | postgres / postgres / geoforraje |

### Comandos Útiles
```bash
make help           # Ver todos los comandos
make logs           # Ver logs de todos los servicios
make backend-shell  # Shell en contenedor backend
make frontend-shell # Shell en contenedor frontend
make migrate        # Aplicar migraciones
make migrate-create MSG="descripción"  # Nueva migración
make lint           # Lint backend + frontend
make test           # Tests backend + frontend
make verify-phase1  # Verificación completa Fase 1
make down           # Bajar servicios
make clean          # Limpiar todo
```

## Estructura del Proyecto
```
geoforraje/
├── backend/
│   ├── app/
│   │   ├── api/           # Dependencias FastAPI
│   │   ├── core/          # Config, security
│   │   ├── db/            # Database, session
│   │   ├── models/        # SQLModel models
│   │   ├── routers/       # API endpoints
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   ├── workers/       # Background tasks
│   │   └── utils/         # Utilidades
│   ├── alembic/           # Migraciones
│   ├── tests/             # Tests pytest
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/    # Componentes compartidos
│   │   ├── pages/         # Páginas principales
│   │   ├── modules/       # Módulos por feature
│   │   │   ├── auth/      # Autenticación
│   │   │   ├── lots/      # Gestión de lotes
│   │   │   ├── map/       # Mapa interactivo
│   │   │   └── results/   # Resultados análisis
│   │   ├── hooks/         # Custom hooks
│   │   ├── types/         # Tipos TypeScript
│   │   └── styles/        # Estilos globales
│   ├── Dockerfile
│   └── package.json
├── shared/
│   └── schemas/           # Contratos compartidos
├── spec/
│   └── printable/         # Especificación por fases
├── docker-compose.yml
├── docker-compose.prod.yml
├── Makefile
└── README.md
```

## Fases de Desarrollo

| Fase | Descripción | Estado |
|------|-------------|--------|
| 1 | Repositorio, README, modelo de datos | ✅ Completada |
| 2 | Autenticación y usuarios | ⏳ Pendiente |
| 3 | CRUD de lotes | ⏳ Pendiente |
| 4 | Integración Leaflet y geometrías | ⏳ Pendiente |
| 5 | Análisis raster y despliegue | ⏳ Pendiente |

Ver `spec/printable/` para especificación detallada por fase.

## Variables de Entorno

### Backend (`.env`)
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

### Frontend (`.env`)
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=GeoForraje 1.0
```

## Testing
```bash
# Backend
make backend-test           # Tests con coverage
make backend-test-watch     # Modo watch

# Frontend
make frontend-test          # Tests unitarios (vitest)
make frontend-test-ui       # Con interfaz visual
```

## Linting & Formatting
```bash
make lint        # Ejecuta ruff + mypy (backend) y eslint + prettier (frontend)
make fmt         # Formatea código (ruff format + prettier)
```

## Migraciones
```bash
make migrate              # Aplicar migraciones pendientes
make migrate-create MSG="add user fields"  # Crear nueva
make migrate-history      # Ver historial
make migrate-downgrade    # Revertir última
```

## Despliegue Producción
```bash
# Build imágenes producción
make ci-build

# Deploy con docker-compose.prod.yml
docker compose -f docker-compose.prod.yml up -d

# Incluye:
# - Nginx reverse proxy con SSL (Let's Encrypt)
# - Backend con Gunicorn + Uvicorn workers
# - Frontend servido por Nginx estático
# - PostgreSQL + PostGIS
# - Redis (para Celery en FASE 5)
# - Prometheus + Grafana (monitoreo)
```

## Licencia
Proyecto académico - Tecnicatura Universitaria en Programación - Programación IV - 2026