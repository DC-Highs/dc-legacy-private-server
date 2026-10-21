# syntax=docker/dockerfile:1

# --- web client ---------------------------------------------------------------
FROM node:22-alpine AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- server -------------------------------------------------------------------
FROM python:3.12-slim AS app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

RUN pip install "poetry>=2.1,<3" \
    && useradd --create-home --uid 10001 dragon

WORKDIR /app
COPY pyproject.toml poetry.lock README.md LICENSE ./
COPY src ./src
RUN poetry install --only main

# Game data: the config/template/PvP seeds are small and baked in; the Flash files, the
# assets (hundreds of MB) and the mapped domains are mounted by compose.yaml.
COPY web/srv /app/seed
COPY --from=web /web/dist /app/frontend/dist
COPY docker/entrypoint.sh docker/gunicorn.conf.py /app/docker/
RUN chmod +x /app/docker/entrypoint.sh

ENV SEED_DIR=/app/seed \
    FRONTEND_DIST=/app/frontend/dist \
    FLASH_DIR=/data/flash \
    ASSETS_DIR=/data/assets \
    DOMAIN_MAP_DIR=/data/domains \
    TRUST_PROXY=false

USER dragon
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8080/api/game/health', timeout=4)"

ENTRYPOINT ["/app/docker/entrypoint.sh"]
