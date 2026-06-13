FROM node:24-alpine AS frontend-builder

WORKDIR /app/frontend

ARG VITE_VAPID_PUBLIC_KEY=
ENV VITE_VAPID_PUBLIC_KEY=${VITE_VAPID_PUBLIC_KEY}

COPY frontend/package*.json ./
RUN npm ci

COPY frontend ./
RUN npm run build

FROM python:3.13-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/app/backend-venv
ENV PLAYWRIGHT_BROWSERS_PATH=/app/.cache/ms-playwright

WORKDIR /app/backend

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        fonts-liberation \
        fonts-unifont \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libatspi2.0-0 \
        libcups2 \
        libdrm2 \
        libgbm1 \
        libnspr4 \
        libnss3 \
        libpq-dev \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxkbcommon0 \
        libxrandr2 \
    && rm -rf /var/lib/apt/lists/*

ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd -g ${APP_GID} app && useradd -u ${APP_UID} -g app -d /app app

COPY backend/pyproject.toml backend/uv.lock* /app/backend/
RUN uv sync --no-cache
RUN uv run playwright install chromium

COPY backend /app/backend
COPY docker/nginx/nginx.conf /app/nginx/default.conf
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist
COPY docker/backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN mkdir -p /app/backend/media /app/backend/staticfiles /app/runtime/frontend /app/runtime/nginx \
    && chown -R app:app /app

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
