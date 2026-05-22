.PHONY: test test-fast test-ui test-ui-chromium test-ui-firefox test-all test-mutation-core test-mutation playwright-install playwright-install-deps

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

test-mutation-core:
	uv run python scripts/run_mutmut_core.py

test-mutation:
	uv run mutmut run

playwright-install:
	uv run playwright install chromium firefox

playwright-install-deps:
	uv run playwright install-deps chromium firefox
