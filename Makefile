# GeoForraje - Makefile
.PHONY: help dev up down logs backend-shell frontend-shell lint test migrate clean verify-phase1 ci-build

# ============================================
# DOCKER - Desarrollo
# ============================================
up: ## Levantar entorno desarrollo
	docker compose up -d --build

down: ## Bajar entorno desarrollo
	docker compose down -v

logs: ## Ver logs
	docker compose logs -f

backend-shell: ## Shell backend
	docker compose exec backend bash

frontend-shell: ## Shell frontend
	docker compose exec frontend sh

# ============================================
# BACKEND - Desarrollo
# ============================================
backend-lint: ## Lint backend
	docker compose exec backend sh -c "cd /app && ruff check . && mypy app"

backend-fmt: ## Formatear backend
	docker compose exec backend sh -c "cd /app && ruff format ."

backend-test: ## Tests backend
	docker compose exec backend sh -c "cd /app && pytest -v --cov=app --cov-report=term-missing"

# Migraciones
migrate: ## Aplicar migraciones
	docker compose exec backend sh -c "cd /app && alembic upgrade head"

migrate-create: ## Nueva migración (uso: make migrate-create MSG="descripcion")
	docker compose exec backend sh -c "cd /app && alembic revision --autogenerate -m '$(MSG)'"

migrate-history: ## Historial migraciones
	docker compose exec backend sh -c "cd /app && alembic history --verbose"

# DB
db-shell: ## psql
	docker compose exec postgres psql -U postgres -d geoforraje

# ============================================
# FRONTEND - Desarrollo
# ============================================
frontend-lint: ## Lint frontend
	docker compose exec frontend sh -c "npm run lint"

frontend-fmt: ## Formatear frontend
	docker compose exec frontend sh -c "npm run format"

frontend-test: ## Tests frontend
	docker compose exec frontend sh -c "npm run test"

frontend-typecheck: ## Typecheck
	docker compose exec frontend sh -c "npm run typecheck"

frontend-build: ## Build producción
	docker compose exec frontend sh -c "npm run build"

# ============================================
# GENERAL
# ============================================
lint: backend-lint frontend-lint ## Lint todo

fmt: backend-fmt frontend-fmt ## Formatear todo

test: backend-test frontend-test ## Tests todo

verify-phase1: ## Verificar Fase 1
	@echo "🔍 Verificando Fase 1..."
	@docker compose ps --format "table {{.Name}}\t{{.Status}}"
	@curl -s http://localhost:8000/health | jq .
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs && echo " OK"
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 && echo " OK"
	@docker compose exec backend sh -c "cd /app && alembic current"
	@docker compose exec postgres psql -U postgres -d geoforraje -c "\dt"
	@make lint

# ============================================
# PRODUCCIÓN
# ============================================
ci-build: ## Build imágenes producción
	docker build -t geoforraje-backend:latest -f backend/Dockerfile.prod backend
	docker build -t geoforraje-frontend:latest -f frontend/Dockerfile.prod frontend

prod-up: ## Levantar producción
	docker compose -f docker-compose.prod.yml up -d --build

prod-down: ## Bajar producción
	docker compose -f docker-compose.prod.yml down -v

prod-logs: ## Logs producción
	docker compose -f docker-compose.prod.yml logs -f

prod-shell-backend: ## Shell backend prod
	docker compose -f docker-compose.prod.yml exec backend bash

# ============================================
# GENERACIÓN
# ============================================
gen-types: ## Generar tipos TS desde OpenAPI
	docker compose exec backend sh -c "cd /app && python -c \"import json; from app.main import app; print(json.dumps(app.openapi()))\" " > openapi.json
	cd frontend && npx openapi-typescript ../openapi.json -o src/types/api.ts

# ============================================
# LIMPIEZA
# ============================================
clean: ## Limpiar contenedores y volúmenes
	docker compose down -v --remove-orphans --rmi local
	docker system prune -f

clean-all: ## Limpieza total
	docker compose down -v --remove-orphans --rmi all
	rm -rf backend/.pytest_cache backend/__pycache__ frontend/node_modules frontend/dist
	docker system prune -af --volumes

.DEFAULT_GOAL := help

help: ## Mostrar ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'