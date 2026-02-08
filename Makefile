# Django Finance - Makefile
# Run 'make help' for available targets

.PHONY: help install up down restart logs migrate makemigrations \
        test test-cov test-unit test-integration lint lint-fix format typecheck \
        security security-bandit security-deps security-report \
        import-check contract-check ci shell runserver createsuperuser clean \
        frontend-install frontend-dev frontend-build frontend-export frontend-clean

# Default target
.DEFAULT_GOAL := help

# =============================================================================
# Help
# =============================================================================
help: ## Show this help message
	@echo "Django Finance - Development Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# =============================================================================
# Installation
# =============================================================================
install: ## Install dependencies
	pip install -e ".[dev]"
	pre-commit install
	pre-commit install --hook-type commit-msg

install-prod: ## Install production dependencies only
	pip install -e ".[production]"

# =============================================================================
# Docker Services
# =============================================================================
up: ## Start Docker services (db, redis)
	docker compose up -d

down: ## Stop Docker services
	docker compose down

restart: ## Restart Docker services
	docker compose restart

logs: ## Tail all service logs
	docker compose logs -f

logs-db: ## Tail database logs
	docker compose logs -f db

logs-redis: ## Tail Redis logs
	docker compose logs -f redis

# =============================================================================
# Database
# =============================================================================
migrate: ## Run database migrations
	python manage.py migrate

makemigrations: ## Create new migrations
	python manage.py makemigrations

showmigrations: ## Show migration status
	python manage.py showmigrations

dbshell: ## Open PostgreSQL shell
	docker compose exec db psql -U postgres -d django_finance

createsuperuser: ## Create admin superuser
	python manage.py createsuperuser

# =============================================================================
# Development
# =============================================================================
runserver: ## Start development server
	daphne -b 0.0.0.0 -p 8000 config.asgi:application

shell: ## Open Django shell
	python manage.py shell

shell-plus: ## Open enhanced Django shell (if django-extensions installed)
	python manage.py shell_plus

# =============================================================================
# Testing
# =============================================================================
test: ## Run test suite
	pytest

test-cov: ## Run tests with coverage report
	pytest --cov --cov-report=term-missing --cov-report=html

test-unit: ## Run only unit tests
	pytest -m unit

test-integration: ## Run only integration tests
	pytest -m integration

test-fast: ## Run tests excluding slow tests
	pytest -m "not slow"

# =============================================================================
# Code Quality
# =============================================================================
lint: ## Run all linters
	ruff check .
	black --check .

lint-fix: ## Auto-fix linting issues
	ruff check --fix .
	black .

format: ## Format code with Black
	black .

typecheck: ## Run mypy type checking
	mypy modules/

security: ## Run all security checks
	@echo "Running Bandit (static security analysis)..."
	bandit -r modules/ shared/ config/ -c pyproject.toml
	@echo ""
	@echo "Running Safety (dependency vulnerability check)..."
	safety check --full-report || true
	@echo ""
	@echo "Running pip-audit (dependency audit)..."
	pip-audit || true
	@echo ""
	@echo "Security scan complete!"

security-bandit: ## Run Bandit security linter only
	bandit -r modules/ shared/ config/ -c pyproject.toml -f json -o security-report.json || true
	bandit -r modules/ shared/ config/ -c pyproject.toml

security-deps: ## Check dependencies for vulnerabilities
	@echo "Running Safety..."
	safety check --full-report
	@echo ""
	@echo "Running pip-audit..."
	pip-audit

security-report: ## Generate security report (JSON)
	@mkdir -p reports
	bandit -r modules/ shared/ config/ -c pyproject.toml -f json -o reports/bandit-report.json || true
	bandit -r modules/ shared/ config/ -c pyproject.toml -f html -o reports/bandit-report.html || true
	safety check --output json > reports/safety-report.json 2>&1 || true
	pip-audit --format json > reports/pip-audit-report.json 2>&1 || true
	@echo "Security reports generated in reports/ directory"

# =============================================================================
# CI Checks
# =============================================================================
import-check: ## Check import boundaries
	@echo "Import boundary checks (import-linter)"
	@echo "Configure import-linter in pyproject.toml when modules are created"
	# import-linter

contract-check: ## Validate API contracts
	@echo "Contract validation"
	@echo "Run when API endpoints are implemented"
	# python manage.py spectacular --validate --fail-on-warn

ci: lint typecheck security test ## Run full CI pipeline locally
	@echo "All CI checks passed!"

# =============================================================================
# Celery
# =============================================================================
worker: ## Start Celery worker
	celery -A config worker -l INFO

beat: ## Start Celery beat scheduler
	celery -A config beat -l INFO

flower: ## Start Flower monitoring (port 5555)
	celery -A config flower --port=5555

# =============================================================================
# Frontend (Next.js React Dashboard)
# =============================================================================
frontend-install: ## Install frontend dependencies
	cd frontend && npm install

frontend-dev: ## Start frontend development server
	cd frontend && npm run dev

frontend-build: ## Build frontend for production
	cd frontend && npm run build

frontend-export: ## Export frontend to static/react/
	cd frontend && npm run build
	rm -rf static/react/ 2>/dev/null || true
	mkdir -p static/react
	cp -r frontend/out/* static/react/

frontend-clean: ## Clean frontend build artifacts
	rm -rf frontend/node_modules 2>/dev/null || true
	rm -rf frontend/.next 2>/dev/null || true
	rm -rf frontend/out 2>/dev/null || true
	rm -rf static/react 2>/dev/null || true

# =============================================================================
# Cleanup
# =============================================================================
clean: ## Clean build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
