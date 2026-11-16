.PHONY: assets ui-install ui-dev ui-build frontend-test test test-fast test-ui test-ui-chromium test-ui-firefox test-all playwright-install playwright-install-deps

assets:
	uv run scripts/download_assets.py

ui-install:
	cd frontend && npm ci

# Vite dev server with hot reload; proxies /api, /events, /assets to the server on :5000
ui-dev:
	cd frontend && npm run dev

ui-build:
	cd frontend && npm run build

frontend-test:
	cd frontend && npm test

test: test-fast

test-fast:
	uv run pytest tests/unit tests/api --cov=. --cov-report=term-missing --cov-fail-under=60

test-ui:
	uv run pytest tests/ui --browser chromium --browser firefox --no-cov

test-ui-chromium:
	uv run pytest tests/ui --browser chromium --no-cov

test-ui-firefox:
	uv run pytest tests/ui --browser firefox --no-cov

test-all:
	uv run pytest tests/unit tests/api --cov=. --cov-report=term-missing --cov-fail-under=60
	uv run pytest tests/ui --browser chromium --browser firefox --no-cov

playwright-install:
	uv run playwright install chromium firefox

playwright-install-deps:
	uv run playwright install-deps chromium firefox
