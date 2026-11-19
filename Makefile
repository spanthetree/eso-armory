.PHONY: run up down upgrade assets ui-install ui-dev ui-build frontend-test test test-fast test-ui test-all playwright-install playwright-install-deps

# From source: the server on the configured port (5000 by default). PORT=8080 make run picks another.
run:
	uv run python -m app $(if $(PORT),--port $(PORT))

# Docker: start, stop, and upgrade to the latest published image (data in ./uploads and ./assets is kept).
up:
	docker compose up -d

down:
	docker compose down

upgrade:
	docker compose pull && docker compose up -d

assets:
	uv run scripts/download_assets.py

ui-install:
	cd frontend && npm ci

frontend/node_modules: frontend/package-lock.json
	cd frontend && npm ci
	touch frontend/node_modules

# Vite dev server with hot reload; proxies /api, /events, /assets to the server on :5000
ui-dev:
	cd frontend && npm run dev

ui-build: frontend/node_modules
	cd frontend && npm run build

frontend-test: frontend/node_modules
	cd frontend && npm test

test: test-fast

test-fast:
	uv run pytest tests/unit tests/api --cov=app --cov-report=term-missing --cov-fail-under=60

# Chromium only: folder watching needs a Chromium browser, and Firefox doubled the run for little coverage.
test-ui: ui-build
	uv run pytest tests/ui --browser chromium --no-cov

test-all: ui-build frontend-test
	uv run pytest tests/unit tests/api --cov=app --cov-report=term-missing --cov-fail-under=60
	uv run pytest tests/ui --browser chromium --no-cov

playwright-install:
	uv run playwright install chromium

playwright-install-deps:
	uv run playwright install-deps chromium
