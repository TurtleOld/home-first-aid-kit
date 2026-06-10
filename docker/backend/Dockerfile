FROM python:3.13-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/app/backend-venv

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

COPY backend/pyproject.toml backend/uv.lock* /app/backend/
RUN uv sync --no-cache
RUN uv run playwright install chromium

COPY backend /app/backend

EXPOSE 8000
