# Django Finance - Makefile
# Run 'make help' for available targets

.PHONY: help install up down restart logs migrate makemigrations \
        test test-cov test-unit test-integration lint lint-fix format typecheck \
        security import-check contract-check ci shell runserver createsuperuser clean

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

security: ## Run security checks
	bandit -r modules/ -c pyproject.toml

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
