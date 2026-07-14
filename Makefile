# SLIC Django development Makefile

MANAGE = uv run python manage.py
PROJECT_NAME = slic

# Development server
runserver:
	$(MANAGE) runserver

# Database operations
migrations:
	$(MANAGE) makemigrations

migrate:
	$(MANAGE) migrate

# System checks
check:
	$(MANAGE) check --fail-level WARNING
	$(MANAGE) makemigrations --check --dry-run

# User management
superuser:
	$(MANAGE) createsuperuser

# Static files
static:
	$(MANAGE) collectstatic --noinput

# Django shell
shell:
	$(MANAGE) shell

# Tests
test:
	uv run pytest tests/unit/ -q

test-all:
	uv run pytest tests/ --ignore=tests/e2e -q

# Clean compiled Python files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# Dependencies
install:
	uv sync --extra dev

# Versioning
bump-patch:
	uv run bump-my-version bump patch

bump-minor:
	uv run bump-my-version bump minor

bump-major:
	uv run bump-my-version bump major

# Help
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Development"
	@echo "  runserver    Start the development server"
	@echo "  shell        Open the Django shell"
	@echo "  install      Install dependencies (uv sync --extra dev)"
	@echo ""
	@echo "Database"
	@echo "  migrations   Create new migrations"
	@echo "  migrate      Apply migrations"
	@echo "  check        Run Django system checks"
	@echo ""
	@echo "Testing"
	@echo "  test         Run unit tests"
	@echo "  test-all     Run all tests excluding e2e"
	@echo ""
	@echo "Deployment"
	@echo "  static       Collect static files"
	@echo "  superuser    Create a superuser"
	@echo ""
	@echo "Versioning"
	@echo "  bump-patch   x.y.Z"
	@echo "  bump-minor   x.Y.0"
	@echo "  bump-major   X.0.0"
	@echo ""
	@echo "  clean        Remove .pyc files and __pycache__ dirs"

.DEFAULT_GOAL := help

.PHONY: help runserver migrations migrate check superuser static shell test test-all clean install bump-patch bump-minor bump-major
