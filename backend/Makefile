# ============================================================================
# Atlas Data Pipeline Platform - Development Makefile
# ============================================================================

.PHONY: help install dev test lint format type-check security clean docker-up docker-down pre-commit

# Default target
.DEFAULT_GOAL := help

# Colors for terminal output
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Atlas Data Pipeline Platform - Development Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(GREEN)<target>$(NC)\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# ============================================================================
# Installation & Setup
# ============================================================================

install: ## Install all dependencies with uv
	@echo "$(BLUE)Installing dependencies...$(NC)"
	uv pip install -e ".[dev]"
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-pre-commit: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

setup: install install-pre-commit ## Complete development setup
	@echo "$(GREEN)✓ Development environment ready$(NC)"

# ============================================================================
# Development
# ============================================================================

dev: ## Start development server
	@echo "$(BLUE)Starting development server...$(NC)"
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-debug: ## Start development server with debug logging
	@echo "$(BLUE)Starting development server with debug logging...$(NC)"
	LOG_LEVEL=DEBUG uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

shell: ## Start IPython shell with app context
	@echo "$(BLUE)Starting IPython shell...$(NC)"
	ipython

# ============================================================================
# Testing
# ============================================================================

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest -v

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest -v -m "unit"

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest -v -m "integration"

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest -v --cov=app --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated at htmlcov/index.html$(NC)"

test-coverage-xml: ## Run tests with XML coverage (for CI)
	@echo "$(BLUE)Running tests with XML coverage...$(NC)"
	pytest -v --cov=app --cov-report=xml --cov-report=term-missing

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	pytest-watch

# ============================================================================
# Code Quality
# ============================================================================

lint: ## Run all linting checks
	@echo "$(BLUE)Running linting checks...$(NC)"
	ruff check app tests
	@echo "$(GREEN)✓ Linting passed$(NC)"

lint-fix: ## Fix auto-fixable linting issues
	@echo "$(BLUE)Fixing linting issues...$(NC)"
	ruff check app tests --fix
	@echo "$(GREEN)✓ Linting issues fixed$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	black app tests
	isort app tests
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-check: ## Check code formatting without modifying
	@echo "$(BLUE)Checking code formatting...$(NC)"
	black --check app tests
	isort --check-only app tests
	@echo "$(GREEN)✓ Formatting is correct$(NC)"

type-check: ## Run mypy type checking
	@echo "$(BLUE)Running type checking...$(NC)"
	mypy app
	@echo "$(GREEN)✓ Type checking passed$(NC)"

security: ## Run security scanning with bandit
	@echo "$(BLUE)Running security scan...$(NC)"
	bandit -r app -f json -o bandit-report.json
	bandit -r app
	@echo "$(GREEN)✓ Security scan complete$(NC)"

pre-commit: ## Run all pre-commit hooks
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	pre-commit run --all-files
	@echo "$(GREEN)✓ Pre-commit checks passed$(NC)"

quality: format lint type-check security ## Run all quality checks
	@echo "$(GREEN)✓ All quality checks passed$(NC)"

# ============================================================================
# Database
# ============================================================================

db-upgrade: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	alembic upgrade head
	@echo "$(GREEN)✓ Database upgraded$(NC)"

db-downgrade: ## Rollback last database migration
	@echo "$(BLUE)Rolling back database migration...$(NC)"
	alembic downgrade -1
	@echo "$(GREEN)✓ Database downgraded$(NC)"

db-migration: ## Create new database migration
	@echo "$(BLUE)Creating new migration...$(NC)"
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"
	@echo "$(GREEN)✓ Migration created$(NC)"

db-reset: ## Reset database (WARNING: destroys all data)
	@echo "$(RED)WARNING: This will destroy all database data!$(NC)"
	@read -p "Are you sure? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		alembic downgrade base; \
		alembic upgrade head; \
		echo "$(GREEN)✓ Database reset complete$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

# ============================================================================
# Docker
# ============================================================================

docker-up: ## Start all Docker services
	@echo "$(BLUE)Starting Docker services...$(NC)"
	docker compose up -d
	@echo "$(GREEN)✓ Docker services started$(NC)"

docker-down: ## Stop all Docker services
	@echo "$(BLUE)Stopping Docker services...$(NC)"
	docker compose down
	@echo "$(GREEN)✓ Docker services stopped$(NC)"

docker-logs: ## Show Docker logs
	docker compose logs -f

docker-build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker compose build
	@echo "$(GREEN)✓ Docker images built$(NC)"

docker-rebuild: ## Rebuild and restart Docker services
	@echo "$(BLUE)Rebuilding Docker services...$(NC)"
	docker compose down
	docker compose build
	docker compose up -d
	@echo "$(GREEN)✓ Docker services rebuilt$(NC)"

docker-clean: ## Remove all Docker volumes and containers
	@echo "$(RED)WARNING: This will remove all Docker volumes!$(NC)"
	@read -p "Are you sure? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker compose down -v; \
		echo "$(GREEN)✓ Docker cleaned$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

# ============================================================================
# Cleaning
# ============================================================================

clean: ## Clean temporary files and caches
	@echo "$(BLUE)Cleaning temporary files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf htmlcov coverage.xml .coverage bandit-report.json 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned$(NC)"

clean-all: clean docker-clean ## Deep clean including Docker
	@echo "$(GREEN)✓ Deep clean complete$(NC)"

# ============================================================================
# Monitoring & Metrics
# ============================================================================

metrics: ## Show Prometheus metrics endpoint
	@echo "$(BLUE)Fetching metrics...$(NC)"
	@curl -s http://localhost:8000/metrics || echo "$(RED)Error: Server not running$(NC)"

health: ## Check application health
	@echo "$(BLUE)Checking health...$(NC)"
	@curl -s http://localhost:8000/api/v1/health | python -m json.tool || echo "$(RED)Error: Server not running$(NC)"

# ============================================================================
# CI/CD
# ============================================================================

ci: format-check lint type-check test-coverage-xml security ## Run all CI checks locally
	@echo "$(GREEN)✓ All CI checks passed$(NC)"

ci-test: ## Run CI test workflow locally
	@echo "$(BLUE)Running CI test workflow...$(NC)"
	docker compose -f docker-compose.yml -f docker-compose.ci.yml up --abort-on-container-exit --exit-code-from test

# ============================================================================
# Documentation
# ============================================================================

docs: ## Generate API documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@echo "$(GREEN)✓ API docs available at http://localhost:8000/docs$(NC)"

docs-serve: dev ## Serve documentation (alias for dev)

# ============================================================================
# Utility
# ============================================================================

version: ## Show current version
	@echo "$(BLUE)Atlas Data Pipeline Platform$(NC)"
	@python -c "import tomli; print('Version:', tomli.load(open('pyproject.toml', 'rb'))['project']['version'])"

requirements: ## Generate requirements.txt from pyproject.toml
	@echo "$(BLUE)Generating requirements.txt...$(NC)"
	uv pip compile pyproject.toml -o requirements.txt
	@echo "$(GREEN)✓ requirements.txt generated$(NC)"

update-deps: ## Update all dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	uv pip install --upgrade -e ".[dev]"
	pre-commit autoupdate
	@echo "$(GREEN)✓ Dependencies updated$(NC)"
