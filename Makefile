.PHONY: help install dev up down logs lint format typecheck test ci clean

# Default target
help:
	@echo "SignalRoom - Marketing Data Platform"
	@echo ""
	@echo "Setup:"
	@echo "  install      Install dependencies locally (requires uv)"
	@echo "  install-dev  Install with dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  dev          Start Temporal + worker with hot reload"
	@echo "  up           Start all services in background"
	@echo "  down         Stop all services"
	@echo "  logs         Tail logs from all services"
	@echo "  logs-worker  Tail logs from worker only"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint         Run ruff linter"
	@echo "  format       Format code with ruff"
	@echo "  typecheck    Run pyright type checker"
	@echo "  test         Run pytest"
	@echo "  ci           Run all checks (lint + typecheck + test)"
	@echo ""
	@echo "Utilities:"
	@echo "  shell        Open Python shell with project loaded"
	@echo "  temporal-ui  Open Temporal Web UI in browser"
	@echo "  clean        Remove build artifacts and caches"

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

install-browser:
	uv pip install -e ".[browser]"
	playwright install chromium

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

dev:
	docker compose up --build

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

logs-worker:
	docker compose logs -f worker

logs-temporal:
	docker compose logs -f temporal

restart-worker:
	docker compose restart worker

# ---------------------------------------------------------------------------
# Code Quality
# ---------------------------------------------------------------------------

lint:
	ruff check src tests

format:
	ruff format src tests
	ruff check --fix src tests

typecheck:
	pyright src

test:
	pytest tests -v

test-quick:
	pytest tests -v -x --ff

# Run a single test file
# Usage: make test-file FILE=tests/test_foo.py
test-file:
	pytest $(FILE) -v

ci: lint typecheck test

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

shell:
	python -c "from signalroom import *; import code; code.interact(local=dict(globals(), **locals()))"

temporal-ui:
	open http://localhost:8080 || xdg-open http://localhost:8080

# Run a single pipeline manually (for testing)
# Usage: make run-pipeline SOURCE=s3_exports
run-pipeline:
	python -m signalroom.scripts.run_pipeline $(SOURCE)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
