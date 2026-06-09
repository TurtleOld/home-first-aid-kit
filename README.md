# Домашняя аптечка

MVP-приложение для учёта лекарств в домашней аптечке. Каркас фазы 0 содержит Django + DRF backend, Vue 3 + Vite + PWA frontend, dev Docker Compose на SQLite и prod Docker Compose на PostgreSQL.

## Требования

- Docker и Docker Compose
- Node.js 24+ и npm 11+ для локального запуска frontend без Docker
- Python 3.13+ и uv для локального запуска backend без Docker

## Настройка окружения

```bash
cp .env.example .env
```

В локальной разработке `DATABASE_URL` пустой, поэтому Django использует SQLite `backend/db.sqlite3`. PostgreSQL подключается только в prod compose.

## Dev через Docker Compose

```bash
docker compose up --build
```

Сервисы:

- Backend: http://localhost:8000/api/
- Healthcheck API: http://localhost:8000/api/health/
- Frontend: http://localhost:5173/

Dev compose применяет миграции на SQLite и запускает Django `runserver`. Frontend запускается через Vite dev server.

## Prod через Docker Compose

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Prod compose поднимает PostgreSQL, backend на gunicorn и nginx. Nginx отдаёт собранную SPA, проксирует `/api/` в Django и раздаёт `/media/` и `/static/` из Docker volumes.

Перед реальным деплоем задайте в `.env` как минимум `SECRET_KEY`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `POSTGRES_*` и при необходимости `HTTP_PORT`.

## Локальный frontend

```bash
cd frontend
npm install
npm run dev
```

## Локальный backend с SQLite

```bash
cd backend
uv sync
DATABASE_URL= uv run python manage.py migrate
DATABASE_URL= uv run python manage.py runserver
```

Если `uv` установлен в `~/.local/bin`, но не находится в shell, используйте `/home/alexander/.local/bin/uv` или добавьте `~/.local/bin` в `PATH`.

## Структура

```text
backend/      Django project: config + core
frontend/     Vue 3 + Vite + vite-plugin-pwa
docker/       Dockerfiles and nginx config
README.md     запуск dev/prod каркаса
.env.example  переменные окружения
```
