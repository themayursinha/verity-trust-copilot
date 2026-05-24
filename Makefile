VENV ?= .venv
PYTHON ?= $(VENV)/bin/python
RUFF ?= $(VENV)/bin/ruff
MYPY ?= $(VENV)/bin/mypy
NPM ?= npm
NPX ?= npx

.PHONY: test test-python test-js lint format-check typecheck check dev dev-backend dev-frontend build

# ── Development ──────────────────────────────────────────────

dev:
	@echo "Starting backend on http://localhost:8000 and frontend on http://localhost:5173"
	@echo "Run 'make dev-backend' and 'make dev-frontend' in separate terminals for best results."
	docker compose up

dev-backend:
	cd backend && $(PYTHON) -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

dev-frontend:
	cd frontend && $(NPM) run dev

# ── Build ────────────────────────────────────────────────────

build:
	cd frontend && $(NPM) run build

# ── Test ─────────────────────────────────────────────────────

test: test-python test-pyright

test-python:
	$(PYTHON) -m pytest backend/tests -v

test-pyright:
	cd frontend && $(NPX) tsc -b

# ── Lint & Type Check ────────────────────────────────────────

lint:
	$(RUFF) check backend/

format-check:
	$(RUFF) format --check backend/

typecheck:
	$(MYPY) backend/app/

check: lint format-check typecheck test

# ── Docker ───────────────────────────────────────────────────

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# ── Database ─────────────────────────────────────────────────

db-migrate:
	cd backend && $(PYTHON) -m alembic upgrade head

db-downgrade:
	cd backend && $(PYTHON) -m alembic downgrade -1

# ── Setup ────────────────────────────────────────────────────

setup-backend:
	cd backend && $(PYTHON) -m pip install -e ".[dev]"

setup-frontend:
	cd frontend && $(NPM) ci

setup: setup-backend setup-frontend

# ── Keys ─────────────────────────────────────────────────────

generate-keys:
	bash scripts/generate-keys.sh
