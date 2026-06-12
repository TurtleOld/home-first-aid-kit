# Contributing

Процесс разработки для людей. Общую карту модулей и инварианты см. в
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md); конвенции для AI-агентов — в [`AGENTS.md`](AGENTS.md).

## Установка

```bash
cp .env.example .env
cd frontend && npm ci && cd ..
cd backend && uv sync --locked && cd ..
pre-commit install
```

`pre-commit install` — обязательный шаг после клонирования. Хуки (`.pre-commit-config.yaml`) гоняют `ruff`
для backend и `eslint`/`prettier --check` для frontend перед каждым коммитом.

## Тесты и линтеры

| Что | Команда |
|---|---|
| Backend линт | `cd backend && uv run ruff check . && uv run ruff format --check .` |
| Backend тесты | `cd backend && uv run python manage.py test` |
| Backend покрытие | `cd backend && uv run coverage run manage.py test && uv run coverage report --skip-covered` |
| Frontend линт | `cd frontend && npm run lint && npm run format:check` |
| Frontend сборка | `cd frontend && npm run build` |
| Все pre-commit хуки сразу | `pre-commit run --all-files` |

CI (`.github/workflows/ci.yml`) гоняет тот же набор команд на каждый PR и push в `main`.

## Миграции

После изменения моделей в `backend/*/models.py`:

```bash
cd backend
uv run python manage.py makemigrations
uv run python manage.py migrate
```

Сгенерированные файлы миграций коммитятся вместе с изменением модели. Не редактируйте уже применённые миграции
вручную — для новых изменений всегда создавайте новую миграцию.

## Обновление lock-файлов

- `backend/uv.lock` — после изменения зависимостей в `backend/pyproject.toml` выполните `uv lock` (или `uv add`/
  `uv remove`, которые обновляют `uv.lock` сами).
- `frontend/package-lock.json` — после изменения `frontend/package.json` выполните `npm install`.

Версии в `pyproject.toml`/`package.json`/`package-lock.json` управляются [release-please](AGENTS.md#commits-and-releases)
автоматически — не бампайте их руками.

## Операционные задачи без `/admin/`

Django admin в проекте отсутствует осознанно (см. `docs/improvement-plan.md`, раздел 5.2): вся работа с семьёй,
участниками, приглашениями и сбросом паролей доступна через API/UI (`InvitationListCreateView`,
`FamilyMembersView`, `MemberPasswordResetView`, `PasswordChangeView`).

Для разовых ручных правок, которые не покрыты API, используйте Django shell:

```bash
cd backend
uv run python manage.py shell
```

Примеры:

```python
# Вручную деактивировать инвайт (например, истёкший, но всё ещё is_active=True)
from accounts.models import Invitation
Invitation.objects.filter(token="...").update(is_active=False)

# Посмотреть состав семьи
from accounts.models import Membership
list(Membership.objects.filter(family_id=1).values("user__username", "role"))

# Принудительно разлогинить пользователя на всех устройствах
from accounts.views import revoke_all_tokens
from django.contrib.auth import get_user_model
revoke_all_tokens(get_user_model().objects.get(username="..."))
```

Изменения через shell **не попадают** в `ChangeLog` (журнал изменений виден пользователям в UI). Если какая-то
операция нужна часто — это сигнал добавить соответствующий API-эндпоинт, а не тянуться к shell на регулярной
основе.

## Ротация секретов

- **`SECRET_KEY`** — используется и Django, и для подписи JWT (`SIMPLE_JWT["SIGNING_KEY"]` по умолчанию берётся из
  `SECRET_KEY`). При смене все выданные access/refresh-токены становятся невалидными — все пользователи будут
  разлогинены и должны войти заново.
- **VAPID-ключи** (`VITE_VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY`) — при смене все существующие push-подписки
  становятся недействительными. Специально чистить их не нужно: при следующей отправке `pywebpush` вернёт
  404/410, и `notifications/tasks.py::send_push` сам удалит мёртвую подписку. Пользователям нужно будет заново
  включить уведомления в профиле (`ProfileView.vue`).
