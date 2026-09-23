# Fase 1 – Repositorio, README y Modelo de Datos

## 🎯 Objetivo de la Fase
Establecer la fundación técnica del proyecto: repositorio Git estructurado, documentación base (README), modelo de datos PostgreSQL/PostGIS con migraciones iniciales, y configuración de entorno de desarrollo (Docker Compose, variables de entorno, linting).

## 📦 Artefactos Generados en esta Fase
- `.github/workflows/ci.yml` – Pipeline CI: lint, typecheck, test, build
- `docker-compose.yml` – Servicios: postgres+postgis, backend, frontend, pgadmin
- `backend/` – Estructura FastAPI + SQLModel + Alembic
  - `backend/app/main.py` – App factory, CORS, routers, lifespan
  - `backend/app/database.py` – Engine asyncpg, session dependency
  - `backend/app/models/__init__.py` – Modelos SQLModel: User, Lot, Analysis
  - `backend/app/core/config.py` – Settings con Pydantic Settings (env)
  - `backend/app/core/security.py` – Hashing, JWT utils (stubs para Fase 2)
- `backend/alembic/` – Configuración migraciones
  - `alembic.ini`
  - `alembic/env.py` – Async migration runner
  - `alembic/versions/001_initial_schema.py` – DDL users, lots, analyses
- `frontend/` – Estructura React + TypeScript + Vite
  - `frontend/src/main.tsx` – Entry point, providers (QueryClient, Zustand)
  - `frontend/src/App.tsx` – Router principal (React Router v6)
  - `frontend/src/styles/globals.css` – Tailwind base + variables CSS
  - `frontend/src/types/api.ts` – Tipos TypeScript generados desde OpenAPI
- `shared/schemas/` – Contratos compartidos (generados)
- `README.md` – Documentación del proyecto: stack, ejecución, endpoints, arquitectura
- `Makefile` / `justfile` – Comandos frecuentes (dev, test, lint, migrate, build)
- `.env.example` – Plantilla variables de entorno

## 🧩 Detalle Técnico

### Backend (FastAPI + SQLModel)
- **App factory** en `app/main.py`: `create_app()` con lifespan para startup/shutdown (DB pool, workers)
- **Modelos SQLModel** (`app/models/`):
  - `User`: id(UUID), email, hashed_password, full_name, created_at, updated_at
  - `Lot`: id, user_id(FK), name, area_ha, geometry(Geometry), created_at, updated_at
  - `Analysis`: id, lot_id(FK), resource_type(Enum), average_rate, raster_file_reference, analyzed_at
- **Database** (`app/database.py`): `AsyncEngine` con asyncpg, `async_sessionmaker`, dependency `get_session()`
- **Config** (`app/core/config.py`): `Settings` con `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `RASTER_DATA_PATH`
- **Alembic** configurado para migraciones **async** (`alembic/env.py` usa `run_async_migrations`)

### Frontend (React + TypeScript)
- **Vite** + React 18 + TypeScript strict mode
- **Tailwind CSS** + PostCSS + Autoprefixer
- **TanStack Query v5** – `QueryClientProvider` en `main.tsx`
- **Zustand** – Store global `authStore` (inicializado vacío, completado en Fase 2)
- **React Router v6** – Rutas públicas (`/login`, `/register`) y protegidas (layout `PrivateRoutes`)
- **ESLint** (typescript-eslint, react-hooks) + **Prettier** + **Husky** (pre-commit)

### Base de Datos (PostgreSQL/PostGIS)
- **Migración 001** (`alembic/versions/001_initial_schema.py`):
  - `CREATE EXTENSION postgis;`
  - Tabla `users` con PK UUID, email UNIQUE, índices
  - Tabla `lots` con FK `user_id`, geometría `GEOMETRY(POLYGON, 4326)`, índice GIST
  - Tabla `analyses` con FK `lot_id`, ENUM `resource_type`, índices compuestos
  - Triggers `updated_at` en las 3 tablas
  - Vista `lots_con_usuario` (join users+lots)

## ✅ Criterios de Aceptación de la Fase
- [ ] `docker compose up -d` levanta postgres+postgis, backend (8000), frontend (5173), pgadmin (5050) sin errores
- [ ] `alembic upgrade head` aplica migración 001 y crea tablas con índices espaciales y ENUM
- [ ] `SELECT * FROM users;` y `SELECT * FROM geometry_columns WHERE f_table_name='lots';` retornan estructura esperada
- [ ] Backend expone `GET /health` → `{"status":"ok"}` y docs en `/docs` (Swagger UI)
- [ ] Frontend carga en `localhost:5173` sin errores de consola, muestra página base con header
- [ ] `make lint` / `npm run lint` pasan sin warnings en backend y frontend
- [ ] `README.md` documentado: stack, comandos dev, variables entorno, endpoints principales, arquitectura

## 🔗 Dependencias con otras Fases
- **Requisito previo**: Ninguna (fase fundacional)
- **Habilita**: Fase 2 (Auth necesita modelos User, DB, config JWT, estructura backend/frontend)