FROM python:3.12.13-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    ESO_ARMORY_CONFIG=/app/uploads/config.json

WORKDIR /app

# Dependencies first so code changes don't reinstall them.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .

# assets/ and uploads/ become volumes; create them owned by the app user so the volumes inherit it.
RUN useradd --system --uid 10001 --home-dir /app armory \
    && mkdir -p assets uploads logs \
    && chown -R armory:armory assets uploads logs

USER armory
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/status', timeout=4)"

ENTRYPOINT ["./docker-entrypoint.sh"]
