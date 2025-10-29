# =============================================================================
# Makefile para Proyecto Lunt
# =============================================================================
# Proporciona comandos shortcuts para desarrollo, testing, y auditoría
#
# Uso:
#   make help          - Muestra ayuda
#   make audit         - Ejecuta auditoría completa
#   make lint          - Ejecuta linters Python y Web
#   make test          - Ejecuta tests
#   make dev           - Levanta entorno de desarrollo
# =============================================================================

.DEFAULT_GOAL := help
.PHONY: help audit audit-quick lint lint-py lint-web test test-py test-web dev up down clean setup-py setup-web setup docker-validate api-health seed

# Colores para output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Variables
PYTHON := python3
PIP := pip
VENV := venv
VENV_ACTIVATE := source $(VENV)/bin/activate
DOCKER_COMPOSE := docker compose
NPM := npm

# =============================================================================
# Help
# =============================================================================

help: ## Muestra esta ayuda
	@echo "$(BLUE)═══════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  Lunt - Makefile Commands$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Tip: Ejecuta 'make audit' para verificar el estado completo del proyecto$(NC)"
	@echo ""

# =============================================================================
# Auditoría
# =============================================================================

audit: ## 🔍 Ejecuta auditoría completa del proyecto
	@echo "$(BLUE)═══════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  Ejecutando Auditoría Completa$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════$(NC)"
	@bash audits/run_local_audit.sh
	@echo ""
	@echo "$(GREEN)✅ Auditoría completada. Revisa audits/history/ para resultados.$(NC)"

audit-quick: ## ⚡ Auditoría rápida (solo lint + structure)
	@echo "$(BLUE)Running quick audit (structure + lint only)...$(NC)"
	@bash -c 'source audits/run_local_audit.sh && check_01_structure && check_02_lint_python && check_03_lint_web'

# =============================================================================
# Linting
# =============================================================================

lint: lint-py lint-web ## 🧹 Ejecuta linters Python + Web

lint-py: ## 🐍 Lint Python con ruff + black
	@echo "$(BLUE)Linting Python code...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(RED)❌ Virtual environment no encontrado. Ejecuta 'make setup-py' primero.$(NC)"; \
		exit 1; \
	fi
	@$(VENV_ACTIVATE) && ruff check api/ scripts/ --fix || true
	@$(VENV_ACTIVATE) && black api/ scripts/ --check

lint-web: ## 🌐 Lint Web con eslint + prettier
	@echo "$(BLUE)Linting Web code...$(NC)"
	@if [ ! -d "web/node_modules" ]; then \
		echo "$(RED)❌ node_modules no encontrado. Ejecuta 'make setup-web' primero.$(NC)"; \
		exit 1; \
	fi
	@cd web && $(NPM) run lint || true
	@cd web && $(NPM) run format:check || true

lint-fix: ## 🔧 Auto-fix issues de linting
	@echo "$(BLUE)Auto-fixing lint issues...$(NC)"
	@$(VENV_ACTIVATE) && ruff check api/ scripts/ --fix
	@$(VENV_ACTIVATE) && black api/ scripts/
	@cd web && $(NPM) run lint:fix || true
	@cd web && $(NPM) run format || true
	@echo "$(GREEN)✅ Lint fixes aplicados$(NC)"

# =============================================================================
# Testing
# =============================================================================

test: test-py ## 🧪 Ejecuta todos los tests

test-py: ## 🐍 Ejecuta tests Python con pytest
	@echo "$(BLUE)Running Python tests...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(RED)❌ Virtual environment no encontrado. Ejecuta 'make setup-py' primero.$(NC)"; \
		exit 1; \
	fi
	@$(VENV_ACTIVATE) && PYTHONPATH=. pytest api/tests/ -v --tb=short

test-web: ## 🌐 Ejecuta tests Web (vitest)
	@echo "$(BLUE)Running Web tests...$(NC)"
	@if [ ! -d "web/node_modules" ]; then \
		echo "$(RED)❌ node_modules no encontrado. Ejecuta 'make setup-web' primero.$(NC)"; \
		exit 1; \
	fi
	@cd web && $(NPM) run test || echo "$(YELLOW)⚠️ No tests configured yet$(NC)"

test-cov: ## 📊 Tests con coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@$(VENV_ACTIVATE) && PYTHONPATH=. pytest api/tests/ -v --cov=api --cov-report=html --cov-report=term
	@echo "$(GREEN)✅ Coverage report generado en htmlcov/index.html$(NC)"

# =============================================================================
# Desarrollo
# =============================================================================

dev: up api-health ## 🚀 Levanta entorno de desarrollo completo
	@echo "$(GREEN)✅ Entorno de desarrollo listo$(NC)"
	@echo "$(BLUE)API: http://localhost:8000$(NC)"
	@echo "$(BLUE)API Docs: http://localhost:8000/docs$(NC)"
	@echo "$(BLUE)Metabase: http://localhost:3000$(NC)"
	@echo "$(BLUE)MinIO: http://localhost:9001$(NC)"

up: ## ⬆️ Levanta servicios Docker
	@echo "$(BLUE)Starting Docker services...$(NC)"
	@$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Servicios iniciados$(NC)"

down: ## ⬇️ Detiene servicios Docker
	@echo "$(BLUE)Stopping Docker services...$(NC)"
	@$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✅ Servicios detenidos$(NC)"

restart: down up ## 🔄 Reinicia servicios Docker

logs: ## 📋 Muestra logs de servicios Docker
	@$(DOCKER_COMPOSE) logs -f

ps: ## 📊 Muestra estado de servicios Docker
	@$(DOCKER_COMPOSE) ps

# =============================================================================
# Setup
# =============================================================================

setup: setup-py setup-web docker-validate ## ⚙️ Setup completo del proyecto
	@echo "$(GREEN)═══════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)  ✅ Setup completo finalizado$(NC)"
	@echo "$(GREEN)═══════════════════════════════════════════════════$(NC)"
	@echo "$(YELLOW)Próximos pasos:$(NC)"
	@echo "  1. $(BLUE)make up$(NC)        - Levantar servicios"
	@echo "  2. $(BLUE)make migrate$(NC)   - Ejecutar migraciones"
	@echo "  3. $(BLUE)make seed$(NC)      - Cargar datos de prueba"
	@echo "  4. $(BLUE)make dev$(NC)       - Verificar entorno"

setup-py: ## 🐍 Setup entorno Python
	@echo "$(BLUE)Setting up Python environment...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(YELLOW)Creating virtual environment...$(NC)"; \
		$(PYTHON) -m venv $(VENV); \
	fi
	@$(VENV_ACTIVATE) && $(PIP) install --upgrade pip
	@$(VENV_ACTIVATE) && $(PIP) install -r requirements.txt
	@if [ -f requirements-dev.txt ]; then \
		$(VENV_ACTIVATE) && $(PIP) install -r requirements-dev.txt; \
	fi
	@echo "$(GREEN)✅ Python environment configurado$(NC)"

setup-web: ## 🌐 Setup entorno Web
	@echo "$(BLUE)Setting up Web environment...$(NC)"
	@cd web && $(NPM) ci || $(NPM) install
	@echo "$(GREEN)✅ Web environment configurado$(NC)"

# =============================================================================
# Database
# =============================================================================

migrate: ## 📊 Ejecuta migraciones de Alembic
	@echo "$(BLUE)Running Alembic migrations...$(NC)"
	@$(DOCKER_COMPOSE) exec api alembic upgrade head
	@echo "$(GREEN)✅ Migraciones ejecutadas$(NC)"

migrate-create: ## 📝 Crea nueva migración (uso: make migrate-create MSG="descripcion")
	@if [ -z "$(MSG)" ]; then \
		echo "$(RED)❌ Error: Especifica MSG=\"descripción\" para la migración$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Creating migration: $(MSG)$(NC)"
	@$(DOCKER_COMPOSE) exec api alembic revision --autogenerate -m "$(MSG)"
	@echo "$(GREEN)✅ Migración creada$(NC)"

migrate-history: ## 📜 Muestra historial de migraciones
	@$(DOCKER_COMPOSE) exec api alembic history

migrate-current: ## 📍 Muestra migración actual
	@$(DOCKER_COMPOSE) exec api alembic current

seed: ## 🌱 Carga datos de prueba
	@echo "$(BLUE)Loading seed data...$(NC)"
	@$(DOCKER_COMPOSE) exec api python scripts/load_seed.py
	@echo "$(GREEN)✅ Seed data cargado$(NC)"

db-reset: ## 🔄 Resetea base de datos (⚠️ DESTRUCTIVO)
	@echo "$(RED)⚠️ ADVERTENCIA: Esto eliminará todos los datos$(NC)"
	@read -p "¿Estás seguro? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		echo "$(BLUE)Resetting database...$(NC)"; \
		$(DOCKER_COMPOSE) down -v; \
		$(DOCKER_COMPOSE) up -d postgres; \
		sleep 5; \
		$(DOCKER_COMPOSE) up -d api; \
		sleep 3; \
		make migrate; \
		make seed; \
		echo "$(GREEN)✅ Base de datos reseteada$(NC)"; \
	else \
		echo "$(YELLOW)Operación cancelada$(NC)"; \
	fi

# =============================================================================
# Verificación
# =============================================================================

docker-validate: ## ✅ Valida configuración Docker
	@echo "$(BLUE)Validating Docker Compose config...$(NC)"
	@$(DOCKER_COMPOSE) config > /dev/null && echo "$(GREEN)✅ Docker config válida$(NC)" || echo "$(RED)❌ Docker config inválida$(NC)"

api-health: ## 🏥 Verifica salud de la API
	@echo "$(BLUE)Checking API health...$(NC)"
	@curl -s http://localhost:8000/health | grep -q "healthy" && echo "$(GREEN)✅ API is healthy$(NC)" || echo "$(RED)❌ API no responde$(NC)"

# =============================================================================
# Build
# =============================================================================

build-web: ## 🏗️ Build del frontend
	@echo "$(BLUE)Building Web app...$(NC)"
	@cd web && $(NPM) run build
	@echo "$(GREEN)✅ Build completado en web/dist/$(NC)"

build-docker: ## 🐳 Build de imágenes Docker
	@echo "$(BLUE)Building Docker images...$(NC)"
	@$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✅ Imágenes construidas$(NC)"

# =============================================================================
# Limpieza
# =============================================================================

clean: ## 🧹 Limpia archivos generados
	@echo "$(BLUE)Cleaning generated files...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf htmlcov/ .coverage 2>/dev/null || true
	@rm -rf web/dist/ web/node_modules/.vite 2>/dev/null || true
	@echo "$(GREEN)✅ Archivos temporales eliminados$(NC)"

clean-all: clean down ## 🗑️ Limpieza completa (incluye Docker volumes)
	@echo "$(RED)⚠️ Eliminando virtual environment y node_modules$(NC)"
	@rm -rf $(VENV)
	@rm -rf web/node_modules
	@$(DOCKER_COMPOSE) down -v
	@echo "$(GREEN)✅ Limpieza completa finalizada$(NC)"

# =============================================================================
# Utilidades
# =============================================================================

shell-api: ## 🐚 Shell interactivo en contenedor API
	@$(DOCKER_COMPOSE) exec api bash

shell-db: ## 🐚 Shell PostgreSQL
	@$(DOCKER_COMPOSE) exec postgres psql -U lunt -d lunt_db

deps-py: ## 📦 Actualiza requirements.txt
	@echo "$(BLUE)Updating Python requirements...$(NC)"
	@$(VENV_ACTIVATE) && $(PIP) freeze > requirements.txt
	@echo "$(GREEN)✅ requirements.txt actualizado$(NC)"

deps-web: ## 📦 Actualiza package-lock.json
	@echo "$(BLUE)Updating Web dependencies...$(NC)"
	@cd web && $(NPM) update
	@echo "$(GREEN)✅ package-lock.json actualizado$(NC)"

version: ## 📌 Muestra versiones de herramientas
	@echo "$(BLUE)═══════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  Versiones de Herramientas$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)Python:$(NC)  $$($(PYTHON) --version 2>&1)"
	@echo "$(GREEN)Docker:$(NC)  $$(docker --version 2>&1)"
	@echo "$(GREEN)Docker Compose:$(NC) $$(docker compose version 2>&1)"
	@echo "$(GREEN)Node:$(NC)    $$(node --version 2>&1)"
	@echo "$(GREEN)NPM:$(NC)     $$(npm --version 2>&1)"
	@if [ -d "$(VENV)" ]; then \
		echo "$(GREEN)Ruff:$(NC)    $$( $(VENV_ACTIVATE) && ruff --version 2>&1 )"; \
		echo "$(GREEN)Black:$(NC)   $$( $(VENV_ACTIVATE) && black --version 2>&1 )"; \
		echo "$(GREEN)Pytest:$(NC)  $$( $(VENV_ACTIVATE) && pytest --version 2>&1 )"; \
	fi

info: version ## ℹ️ Información del proyecto
	@echo ""
	@echo "$(BLUE)═══════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  Estado del Proyecto$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)Branch:$(NC)  $$(git branch --show-current 2>/dev/null || echo 'No Git')"
	@echo "$(GREEN)Commit:$(NC)  $$(git rev-parse --short HEAD 2>/dev/null || echo 'No Git')"
	@echo "$(GREEN)Venv:$(NC)    $$([ -d '$(VENV)' ] && echo '✅ Presente' || echo '❌ No encontrado')"
	@echo "$(GREEN)Docker:$(NC)  $$($(DOCKER_COMPOSE) ps --format json 2>/dev/null | jq -r 'length' || echo '0') servicios corriendo"
	@echo ""
