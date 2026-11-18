# Frontend stage: builds the Svelte app into /static/dist; Node stays out of the final image.
FROM node:22.22.0-bookworm-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


# Build stage: uv and its download cache stay here, out of the final image.
FROM python:3.12.13-alpine3.22 AS build

COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project


FROM python:3.12.13-alpine3.22

ENV PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    ESO_ARMORY_CONFIG=/app/uploads/config.json

WORKDIR /app

COPY --from=build /opt/venv /opt/venv

# assets/ and uploads/ become volumes; create them owned by the app user so the volumes inherit it.
RUN addgroup -S armory && adduser -S -D -u 10001 -G armory -h /app armory \
    && mkdir -p assets uploads logs \
    && chown armory:armory assets uploads logs

COPY . .
COPY --from=frontend /static/dist ./static/dist

USER armory
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/status', timeout=4)"

ENTRYPOINT ["./docker-entrypoint.sh"]
