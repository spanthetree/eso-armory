.PHONY: assets ui-install ui-dev ui-build frontend-test test test-fast test-ui test-ui-chromium test-ui-firefox test-all playwright-install playwright-install-deps

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
	uv run pytest tests/unit tests/api --cov=. --cov-report=term-missing --cov-fail-under=60

test-ui: ui-build
	uv run pytest tests/ui --browser chromium --browser firefox --no-cov

test-ui-chromium: ui-build
	uv run pytest tests/ui --browser chromium --no-cov

test-ui-firefox: ui-build
	uv run pytest tests/ui --browser firefox --no-cov

test-all: ui-build frontend-test
	uv run pytest tests/unit tests/api --cov=. --cov-report=term-missing --cov-fail-under=60
	uv run pytest tests/ui --browser chromium --browser firefox --no-cov

playwright-install:
	uv run playwright install chromium firefox

playwright-install-deps:
	uv run playwright install-deps chromium firefox
