# Guía de Contribución - GeoForraje 1.0

¡Gracias por contribuir! Esta guía te ayuda a configurar el entorno y seguir nuestros estándares.

---

## 🚀 Configuración Rápida

```bash
# 1. Clonar y entrar
git clone https://github.com/Elortegui-Guirin/Trabajo-Final-Tecnicatura-Universitaria-en-Programacion.git
cd Trabajo-Final-Tecnicatura-Universitaria-en-Programacion

# 2. Levantar todo (requiere Docker + Docker Compose)
make up

# 3. Verificar
make health
```

**Accesos**: Frontend `localhost:5173` | Backend `localhost:8000/docs` | pgAdmin `localhost:5050`

---

## 🌿 Convenciones de Ramas

| Tipo | Prefijo | Ejemplo |
|------|---------|---------|
| Feature | `feat/` | `feat/lots-filter-by-area` |
| Fix | `fix/` | `fix/login-refresh-token` |
| Docs | `docs/` | `docs/update-readme` |
| Refactor | `refactor/` | `refactor/lot-service` |
| Test | `test/` | `test/auth-endpoints` |
| Chore | `chore/` | `chore/update-deps` |

**Rama base**: `main` (protegida, requiere PR)

---

## 📝 Convenciones de Commits

Usamos **Conventional Commits**:

```
<tipo>[ámbito opcional]: <descripción corta>

[cuerpo opcional]

[pie opcional]
```

| Tipo | Cuándo usar |
|------|-------------|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Solo documentación |
| `refactor` | Refactor sin cambio de comportamiento |
| `test` | Agregar/modificar tests |
| `chore` | Mantenimiento (deps, configs) |
| `style` | Formato, linting (sin lógica) |

**Ejemplos**:
```
feat(lots): agregar filtro por área en listado
fix(auth): corregir rotación refresh token
docs: agregar diagrama ER en diagrama_er.md
refactor(lot-service): extraer validación geometría a geometry_service
test(auth): agregar test login inválido
chore: actualizar dependencias frontend
```

---

## 🔧 Estilo de Código

### Backend (Python)
```bash
# Formatear
make backend-fmt    # ruff format

# Lint + typecheck
make backend-lint   # ruff check + mypy

# Tests
make backend-test   # pytest con coverage
```

**Estándares**:
- Python 3.11+, type hints obligatorios
- Ruff (line-length=100, double quotes)
- mypy strict mode
- Pydantic v2 para schemas

### Frontend (TypeScript/React)
```bash
# Formatear
make frontend-fmt   # prettier --write

# Lint
make frontend-lint  # eslint

# Typecheck
make frontend-typecheck  # tsc --noEmit

# Tests
make frontend-test  # vitest
```

**Estándares**:
- TypeScript strict mode
- ESLint + Prettier (single quotes, trailing commas)
- React Hook Form + Zod para formularios
- TanStack Query para server state
- Zustand para client state

---

## 🔀 Flujo de Pull Request

1. **Crear rama** desde `main` actualizada:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feat/mi-nueva-funcionalidad
   ```

2. **Desarrollar** con commits atómicos y descriptivos

3. **Ejecutar checks locales** antes de push:
   ```bash
   make lint        # backend + frontend
   make test        # backend + frontend
   ```

4. **Push y abrir PR**:
   ```bash
   git push origin feat/mi-nueva-funcionalidad
   # Abrir PR en GitHub hacia main
   ```

5. **PR Template** (completar):
   - **Descripción**: Qué cambia y por qué
   - **Tipo**: Feature / Fix / Docs / Refactor
   - **Testing**: Cómo se probó (manual, tests nuevos)
   - **Screenshots** (si aplica UI)
   - **Breaking changes**: Sí/No

6. **Review**: Mínimo 1 aprobación + CI verde

7. **Merge**: Squash and merge (historial limpio)

---

## 🧪 Testing

```bash
# Todo
make test

# Solo backend
make backend-test

# Solo frontend
make frontend-test

# Coverage
make backend-test     # genera reporte en terminal
make frontend-test    # vitest --coverage
```

**Regla**: Tests nuevos para cada feature/fix. Coverage mínimo 80%.

---

## 📁 Estructura de Archivos (resumen)

```
geoforraje/
├── backend/
│   ├── app/
│   │   ├── routers/       # Endpoints REST
│   │   ├── services/      # Lógica de negocio
│   │   ├── schemas/       # Pydantic models (API contracts)
│   │   ├── models/        # SQLModel (DB models)
│   │   ├── core/          # Config, security
│   │   └── db/            # Database setup
│   ├── tests/             # pytest
│   └── alembic/           # Migraciones
├── frontend/
│   ├── src/
│   │   ├── modules/       # Feature modules (auth, lots, map, results)
│   │   ├── components/    # Componentes compartidos
│   │   ├── hooks/         # Custom hooks
│   │   └── types/         # TypeScript types
│   └── tests/             # vitest
├── spec/printable/        # Spec por fase
├── docs/                  # Documentación adicional
└── docker-compose.yml
```

---

## 🐛 Reportar Issues

Usa las plantillas de GitHub Issues:
- **Bug Report**: Qué falla, pasos para reproducir, esperado vs actual
- **Feature Request**: Qué necesitas, por qué, alternativas consideradas
- **Documentation**: Qué falta o está incorrecto

---

## 📞 Contacto

- **Verónica Guirin** - vguirin@universidad.edu
- **Rosario Elortegui** - relortegui@universidad.edu

---

**Última actualización**: Septiembre 2026