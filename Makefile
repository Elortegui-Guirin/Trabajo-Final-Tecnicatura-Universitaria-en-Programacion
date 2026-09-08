# GeoForraje 1.0 - Makefile
# Uso: make <comando>
# Ver comandos: make help

.PHONY: help dev up down logs backend-frontend lint test migrate shell clean

# Variables
BACKEND_DIR = backend
FRONTEND_DIR = frontend
DOCKER_COMPOSE = docker compose

help: ## Mostrar esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================
# DOCKER - Orquestación completa
# ============================================
up: ## Levantar todos los servicios (detached)
	$(DOCKER_COMPOSE) up -d --build

down: ## Bajar todos los servicios y volúmenes
	$(DOCKER_COMPOSE) down -v

logs: ## Ver logs de todos los servicios
	$(DOCKER_COMPOSE) logs -f

logs-backend: ## Ver logs solo backend
	$(DOCKER_COMPOSE) logs -f backend

logs-frontend: ## Ver logs solo frontend
	$(DOCKER_COMPOSE) logs -f frontend

logs-db: ## Ver logs solo postgres
	$(DOCKER_COMPOSE) logs -f postgres

restart: ## Reiniciar todos los servicios
	$(DOCKER_COMPOSE) restart

ps: ## Estado de contenedores
	$(DOCKER_COMPOSE) ps

# ============================================
# BACKEND - Comandos desarrollo
# ============================================
backend-shell: ## Shell interactivo en contenedor backend
	$(DOCKER_COMPOSE) exec backend bash

backend-lint: ## Lint backend (ruff + mypy)
	$(DOCKER_COMPOSE) exec backend sh -c "cd /app && ruff check . && mypy app"

backend-fmt: ## Formatear backend (ruff format)
	$(DOCKER_COMPOSE) exec backend sh -c "cd /app && ruff format ."

backend-test: ## Tests backend (pytest)
	$(DOCKER_COMPOSE) exec backend sh -c "cd /app && pytest -v --cov=app --cov-report=term-missing"

backend-test-watch: ## Tests en modo watch
	$(DOCKER_COMPOSE) exec backend sh -c "cd /app && pytest-watch --clear --runner 'pytest -v'"

# Migraciones Alembic
migrate: ## Aplicar migraciones (alembic upgrade head)
	$(DOCKER_COMPOSE) exec backend sh -c "cd /app && alembic upgrade head"

migrate-create: ## Crear nueva migración (uso: make migrate-create MSG="descripción")
	$(DOCKER_COMPOSE) exec backend sh -c "cd /app && alembic revision --autogenerate -m '$(MSG)'"

migrate-history: ## Ver historial migraciones
	$(DOCKER_COMPOSE) exec backend sh -c "cd /app && alembic history --verbose"

migrate-current: ## Ver migración actual
	$(DOCKER_COMPOSE) exec backend sh -c "cd /app && alembic current"

migrate-downgrade: ## Revertir última migración
	$(DOCKER_COMPOSE) exec backend sh -c "cd /app && alembic downgrade -1"

# DB directa
db-shell: ## psql en contenedor postgres
	$(DOCKER_COMPOSE) exec postgres psql -U postgres -d geoforraje

db-dump: ## Backup BD a archivo
	$(DOCKER_COMPOSE) exec postgres pg_dump -U postgres geoforraje > backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore: ## Restaurar BD desde archivo (uso: make db-restore FILE=backup.sql)
	$(DOCKER_COMPOSE) exec -T postgres psql -U postgres geoforraje < $(FILE)

# ============================================
# FRONTEND - Comandos desarrollo
# ============================================
frontend-shell: ## Shell interactivo en contenedor frontend
	$(DOCKER_COMPOSE) exec frontend sh

frontend-lint: ## Lint frontend (eslint + prettier check)
	$(DOCKER_COMPOSE) exec frontend sh -c "npm run lint"

frontend-fmt: ## Formatear frontend (prettier write)
	$(DOCKER_COMPOSE) exec frontend sh -c "npm run format"

frontend-test: ## Tests frontend (vitest)
	$(DOCKER_COMPOSE) exec frontend sh -c "npm run test"

frontend-test-ui: ## Tests frontend con UI
	$(DOCKER_COMPOSE) exec frontend sh -c "npm run test:ui"

frontend-build: ## Build producción frontend
	$(DOCKER_COMPOSE) exec frontend sh -c "npm run build"

frontend-typecheck: ## TypeScript type check
	$(DOCKER_COMPOSE) exec frontend sh -c "npm run typecheck"

# ============================================
# LINT GLOBAL (backend + frontend)
# ============================================
lint: backend-lint frontend-lint ## Ejecutar todos los linters

fmt: backend-fmt frontend-fmt ## Formatear todo el código

# ============================================
# TESTS GLOBALES
# ============================================
test: backend-test frontend-test ## Ejecutar todos los tests

# ============================================
# DEV - Atajos comunes
# ============================================
dev: up ## Alias para up (levantar entorno dev)

dev-logs: logs ## Alias para logs

dev-shell: backend-shell ## Alias para backend-shell

# ============================================
# UTILIDADES
# ============================================
clean: ## Limpiar contenedores, volúmenes, imágenes huérfanas
	$(DOCKER_COMPOSE) down -v --remove-orphans --rmi local
	docker system prune -f

clean-all: ## Limpieza agresiva (incluye node_modules, __pycache__, .pytest_cache)
	$(DOCKER_COMPOSE) down -v --remove-orphans --rmi all
	rm -rf $(BACKEND_DIR)/.pytest_cache $(BACKEND_DIR)/__pycache__ $(BACKEND_DIR)/*.pyc
	rm -rf $(FRONTEND_DIR)/node_modules $(FRONTEND_DIR)/dist $(FRONTEND_DIR)/.vite
	docker system prune -af --volumes

health: ## Health check de todos los servicios
	@echo "=== Backend ===" && curl -s http://localhost:8000/health | jq .
	@echo "\n=== Frontend ===" && curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 && echo " OK"
	@echo "\n=== Postgres ===" && $(DOCKER_COMPOSE) exec postgres pg_isready -U postgres
	@echo "\n=== PgAdmin ===" && curl -s -o /dev/null -w "%{http_code}" http://localhost:5050 && echo " OK"

# ============================================
# CI/CD - Comandos para pipeline
# ============================================
ci-lint: ## Lint para CI (sin docker, requiere deps instaladas localmente)
	cd $(BACKEND_DIR) && ruff check . && mypy app
	cd $(FRONTEND_DIR) && npm run lint

ci-test: ## Tests para CI
	cd $(BACKEND_DIR) && pytest -v --cov=app --cov-report=xml
	cd $(FRONTEND_DIR) && npm run test -- --run

ci-build: ## Build imágenes producción
	docker build -t geoforraje-backend:latest -f $(BACKEND_DIR)/Dockerfile.prod $(BACKEND_DIR)
	docker build -t geoforraje-frontend:latest -f $(FRONTEND_DIR)/Dockerfile.prod $(FRONTEND_DIR)

# ============================================
# GENERACIÓN CÓDIGO (OpenAPI -> TypeScript)
# ============================================
gen-types: ## Generar tipos TypeScript desde OpenAPI backend
	$(DOCKER_COMPOSE) exec backend sh -c "cd /app && python -c \"import json; from app.main import app; print(json.dumps(app.openapi()))\" " > openapi.json
	cd $(FRONTEND_DIR) && npx openapi-typescript ../openapi.json -o src/types/api.ts

# ============================================
# VERIFICACIÓN FASE 1
# ============================================
verify-phase1: ## Verificar criterios de aceptación Fase 1
	@echo "🔍 Verificando Fase 1..."
	@echo "\n1. Servicios arriba:"
	@$(DOCKER_COMPOSE) ps --format "table {{.Name}}\t{{.Status}}"
	@echo "\n2. Backend health:"
	@curl -s http://localhost:8000/health | jq .
	@echo "\n3. Swagger docs:"
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs && echo " OK"
	@echo "\n4. Frontend:"
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 && echo " OK"
	@echo "\n5. Migraciones:"
	@$(DOCKER_COMPOSE) exec backend sh -c "cd /app && alembic current"
	@echo "\n6. Tablas e índices:"
	@$(DOCKER_COMPOSE) exec postgres psql -U postgres -d geoforraje -c "\dt" && echo ""
	@$(DOCKER_COMPOSE) exec postgres psql -U postgres -d geoforraje -c "SELECT indexname, indexdef FROM pg_indexes WHERE tablename IN ('users','lots','analyses');"
	@echo "\n7. Vista lots_con_usuario:"
	@$(DOCKER_COMPOSE) exec postgres psql -U postgres -d geoforraje -c "SELECT * FROM lots_con_usuario LIMIT 1;"
	@echo "\n8. Lint:"
	@make lint
	@echo "\n✅ Fase 1 verificada completamente"

# Default
.DEFAULT_GOAL := help