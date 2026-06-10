# Домашняя аптечка

MVP-приложение для учёта лекарств в домашней аптечке. Проект использует Django + DRF backend, Vue 3 + Vite + PWA frontend, dev Docker Compose на SQLite и prod Docker Compose на PostgreSQL.

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
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Prod compose поднимает PostgreSQL, backend на gunicorn и готовый `nginx:1.27-alpine`. Production image `ghcr.io/turtleold/home-first-aid-kit` содержит backend, собранную SPA и nginx config; `docker/backend/entrypoint.sh` при старте копирует SPA и nginx config в Docker volumes, откуда их читает nginx. Nginx проксирует `/api/` в Django и раздаёт `/media/` и `/static/` из Docker volumes.

Перед реальным деплоем задайте в `.env` как минимум:

```dotenv
SECRET_KEY=long-random-secret
DEBUG=false
ALLOWED_HOSTS=firstaid.example.com
CORS_ALLOWED_ORIGINS=https://firstaid.example.com
CSRF_TRUSTED_ORIGINS=https://firstaid.example.com
SECURE_SSL_REDIRECT=true
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
SECURE_HSTS_SECONDS=2592000
POSTGRES_DB=firstaid
POSTGRES_USER=firstaid
POSTGRES_PASSWORD=strong-password
DATABASE_URL=postgres://firstaid:strong-password@db:5432/firstaid
HTTP_PORT=80
```

Production-контейнер nginx слушает HTTP. Завершайте HTTPS на внешнем reverse proxy и передавайте в приложение заголовок `X-Forwarded-Proto: https`; это нужно для `SECURE_SSL_REDIRECT`, secure cookies и установки PWA в браузере.

## CI и публикация Docker-образов

GitHub Actions находятся в `.github/workflows/`:

- `ci.yml` запускает backend tests, frontend build и проверку сборки production Docker-образа.
- `docker-publish.yml` публикует backend production-образ в GitHub Container Registry на push в `main`/`master`, git tags `v*` и ручной `workflow_dispatch`.

Публикуется образ:

```text
ghcr.io/turtleold/home-first-aid-kit
```

Теги формируются из ветки, git tag, commit SHA (`sha-...`) и `latest` для default branch. Образ содержит backend, собранную SPA и nginx config. Prod compose использует этот образ по умолчанию:

```dotenv
BACKEND_IMAGE=ghcr.io/turtleold/home-first-aid-kit:latest
```

Nginx в prod compose использует готовый `nginx:1.27-alpine`; SPA и nginx config подтягиваются из production image через `docker/backend/entrypoint.sh` в named volumes:

```bash
docker login ghcr.io
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

1. Запустите сервисы:

   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

2. Проверьте backend внутри сети или через опубликованный HTTP-порт:

   ```bash
   curl http://localhost:${HTTP_PORT:-80}/api/health/
   ```

3. Откройте внешний HTTPS-адрес, войдите в приложение и проверьте установку PWA в браузере телефона или десктопа.

## PWA

Frontend собирается с `vite-plugin-pwa`: manifest, service worker, precache SPA-оболочки и отдельная офлайн-страница входят в `npm run build`. Media-файлы кэшируются service worker по `CacheFirst`; API-ответы намеренно не кэшируются, чтобы не хранить JWT-зависимые семейные данные в runtime cache.

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

## Auth API

- `POST /api/auth/register` — создать администратора и семью
- `POST /api/auth/login` — получить JWT access/refresh
- `POST /api/auth/refresh` — обновить access-токен
- `GET /api/auth/me` — текущий пользователь, семья и роль
- `GET /api/invitations` — список активных приглашений семьи для admin
- `POST /api/invitations` — создать приглашение для admin
- `GET /api/invitations/{token}` — публичная проверка приглашения
- `POST /api/invitations/{token}/accept` — принять приглашение новым пользователем
- `DELETE /api/invitations/{id}` — отозвать приглашение для admin

## Структура

```text
backend/      Django project: config + accounts + core
frontend/     Vue 3 + Vite + vite-plugin-pwa
docker/       Dockerfiles and nginx config
README.md     запуск dev/prod каркаса
.env.example  переменные окружения
```
