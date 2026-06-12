# Архитектура

Карта модулей и сквозных потоков данных. Цель документа — дать и человеку, и AI-агенту быстрый ответ на
вопрос «куда лезть, чтобы сделать X» и описать инварианты, которые нельзя молча нарушать.

## Модули backend (`backend/`)

Django 5 + DRF, JWT-аутентификация (`rest_framework_simplejwt`).

| Модуль | Зона ответственности |
|---|---|
| `config` | настройки Django, `urls.py` (корневой роутинг), celery (`config/celery.py`) |
| `accounts` | пользователи, семьи (`Family`), членство (`Membership`), приглашения (`Invitation`), аутентификация, смена/сброс пароля |
| `core` | сквозные утилиты: health-check, OpenAPI-схема, журнал изменений (`ChangeLog`), защищённая раздача медиа, валидаторы загрузок, пагинация |
| `medicines` | лекарства (`Medicine`), список покупок (`ShoppingItem`), журнал изменений по ним; `medicines/reference_parser` — парсинг справочника лекарств через Playwright/Chromium |
| `notifications` | push-подписки (`PushSubscription`), celery-задача рассылки напоминаний об истекающих лекарствах |

## Модули frontend (`frontend/src/`)

Vue 3 + Pinia + Vite (PWA).

| Модуль | Зона ответственности |
|---|---|
| `api/client.js` | единая точка HTTP-запросов к `/api`, обработка ошибок, автоматический refresh access-токена |
| `stores/auth.js` | состояние аутентификации (токены, пользователь, семья, роль), хранение токенов в `localStorage` |
| `stores/theme.js` | тема оформления |
| `views/*` | страницы-маршруты: лекарства, список покупок, профиль, приглашения, журнал изменений, регистрация/вход |
| `components/*` | переиспользуемые UI-блоки (поиск по справочнику, превью медиа, скелетоны загрузки и т.п.) |
| `utils/expiry.js` | расчёт статуса срока годности — **дублирует** правила `backend/core/utils.py::compute_expiry_status`, независимая JS-реализация |
| `utils/push.js` | подписка/отписка от web push в Service Worker |

## Инвариант family-scoping (ключевой инвариант безопасности)

Вся пользовательская информация (лекарства, покупки, журнал изменений, push-подписки) принадлежит **семье**
(`accounts.Family`), а не отдельному пользователю. Пользователь состоит в семье через `Membership` (роль `admin`
или `member`).

- `accounts/selectors.py::get_current_membership(user)` / `get_current_family(user)` — текущая семья пользователя
  (берётся первое по `joined_at` членство; на практике у пользователя одно членство).
- `accounts/permissions.py`:
  - `IsFamilyMember` — пользователь состоит в какой-либо семье;
  - `IsFamilyAdmin` — пользователь — админ своей семьи (нужно для управления приглашениями и участниками).
- `medicines/views.py::FamilyScopedModelViewSet` — базовый ViewSet для всех моделей, принадлежащих семье
  (`MedicineViewSet`, `ShoppingItemViewSet`, `ChangeLogViewSet`):
  - `permission_classes = [IsAuthenticated, IsFamilyMember]`;
  - `get_family()` возвращает `get_current_family(request.user)`;
  - запросы автоматически фильтруются и создаются в рамках этой семьи.

**Любой новый эндпоинт, отдающий или принимающий данные конкретной семьи, должен наследоваться от
`FamilyScopedModelViewSet` (или явно фильтровать по `get_current_family(request.user)`/проверять
`IsFamilyMember`/`IsFamilyAdmin`).** Прямой доступ по `pk` без проверки принадлежности к семье — уязвимость
(IDOR).

## Поток аутентификации

1. **Регистрация первого пользователя** (`POST /api/auth/register`, `RegisterView`):
   - доступна только пока в системе нет ни одной семьи (`registration_is_open()` — `not Family.objects.exists()`);
   - создаёт `User`, новую `Family` и `Membership` с ролью `admin`;
   - возвращает пару JWT-токенов (`tokens_for_user`).
2. **Дальнейшие пользователи** добираются только через приглашения (`Invitation` → `/api/invitations/<token>/accept`,
   `InvitationAcceptView`) — получают `Membership` с ролью `member` в семье, выпустившей приглашение.
3. **JWT**: `rest_framework_simplejwt`, `ROTATE_REFRESH_TOKENS=True`, `BLACKLIST_AFTER_ROTATION=True` —
   каждый refresh выдаёт новую пару токенов и блэклистит старый refresh-токен
   (`rest_framework_simplejwt.token_blacklist`).
4. **Logout** (`LogoutView`) — блэклистит переданный refresh-токен.
5. **Смена пароля** (`PasswordChangeView`) и **сброс пароля участнику админом** (`MemberPasswordResetView`) —
   вызывают `revoke_all_tokens(user)`, который блэклистит все выпущенные ранее `OutstandingToken` пользователя:
   после смены пароля все текущие сессии (включая другие устройства) обязаны заново войти.
6. **Frontend**: `stores/auth.js` хранит access/refresh в `localStorage`, `api/client.js` при 401 пытается
   обновить access-токен через refresh и повторяет запрос; при неудаче — разлогин.

## Поток медиа (фото лекарств, файлы инструкций)

1. Загрузка идёт через `MedicineSerializer` (поля `photo`, `instruction_file`), путь генерируется
   `core/uploads.py` (`medicine_photo_upload_to` / `medicine_instruction_upload_to`) —
   `{prefix}/{family_id}/{uuid4}{ext}`, т.е. файлы физически разложены по каталогам семей.
2. Валидация загружаемых файлов — `core/validators.py`: разрешённые расширения, лимит размера (10 МБ),
   проверка магических байт содержимого (PDF/JPEG/PNG/WEBP) — защита от подмены расширения.
3. **Отдача файла** — только через `core/views.py::ProtectedMediaView` (`GET /api/media/<path>`):
   - требует аутентификации (`IsAuthenticated`);
   - парсит путь на `{prefix}/{family_id}/{filename}`, проверяет `prefix` из `PROTECTED_MEDIA_PREFIXES`
     (`medicine_photos`, `medicine_instructions`) и что `family_id` совпадает с семьёй текущего пользователя —
     иначе `403`/`404`;
   - в DEBUG отдаёт файл напрямую (`FileResponse`), в проде — заголовок `X-Accel-Redirect`, который nginx
     перенаправляет на internal-локацию `/protected-media/...` (см. `docker/nginx/*.conf`), физически читающую
     файл с диска без повторной авторизации на уровне nginx — авторизация уже выполнена Django-вьюхой.

## Поток push-уведомлений

1. Frontend подписывается на push через Service Worker (`utils/push.js`), подписка (`endpoint`, `p256dh`, `auth`)
   сохраняется в `notifications.PushSubscription`, привязанной к `User`.
2. Celery beat (`config/celery.py`) по расписанию запускает `notifications/tasks.py::send_expiry_notifications`.
3. Задача проходит по всем `Family` (с `prefetch_related` для лекарств и подписок участников, чтобы не плодить
   N+1 запросы), для каждой семьи строит текстовый дайджест просроченных и заканчивающихся лекарств
   (`build_digest`).
4. Если дайджест не пуст — отправляет push всем `PushSubscription` участников семьи через `pywebpush`
   (`send_push`), используя `VAPID_PRIVATE_KEY`/`VAPID_CLAIMS_EMAIL` из настроек. Если `VAPID_PRIVATE_KEY` не
   задан — задача ничего не делает (push отключён).

## Журнал изменений (`ChangeLog`)

- Модель `core.models.ChangeLog`: `family`, `actor` (может быть `None`, если действие выполнено неаутентифицированным
  способом), `action` (`create`/`update`/`delete`), `entity_type`, `entity_repr`, `changes` (JSON-диф полей),
  `created_at`.
- Пишется автоматически в `FamilyScopedModelViewSet.perform_create/perform_update/perform_destroy` через
  `core/mixins.py`:
  - `snapshot_instance(instance, log_fields)` — снимок значений полей, перечисленных в `log_fields` каждого
    ViewSet (например, `MedicineViewSet.log_fields`);
  - `diff_snapshots(before, after)` — диф «было/стало» только по изменившимся полям;
  - `create_change_log(...)` — создаёт запись.
- Читается через `ChangeLogViewSet` (`/api/changelog`, family-scoped, только для своей семьи) и отображается на
  странице `ChangeLogView.vue`.
- **Инвариант:** любое изменение данных семьи через API должно проходить через `FamilyScopedModelViewSet` (или
  явно вызывать `create_change_log`), чтобы попасть в журнал. Прямые правки через `manage.py shell` (см.
  `CONTRIBUTING.md`) в журнал не попадают — это осознанный компромисс для редких операционных задач.

## Связанные документы

- [`AGENTS.md`](../AGENTS.md) — конвенции для AI-агентов (стиль кода, коммиты, релизы, CI/CD).
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — процесс разработки для людей.
