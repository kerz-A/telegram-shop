# 🛒 Telegram Shop Bot

Полнофункциональный интернет-магазин в Telegram: **бот** (Aiogram 3), **админ-панель** (Django 5 + DRF) и **Mini App** (React + TypeScript).

Весь проект поднимается **одной командой**: `docker-compose up --build`

---

## Архитектура

```
┌──────────────────┐                  ┌──────────────────┐
│  Telegram Bot     │   Shared DB     │  Django Admin     │
│  Aiogram 3        │◄──────────────►│  + REST API (DRF) │
│  SQLAlchemy async │   (PostgreSQL)  │                    │
└────────┬─────────┘                  └────────┬───────────┘
         │                                      │
         │◄─── HTTP Webhook (POST :8081) ───────┘
         │     (статус заказа, рассылки,
         │      новые заказы из WebApp)
         │
         │     ┌──────────────────────────────┐
         │     │  React Mini App (WebApp)      │
         │     │  nginx → proxy /api/ → Django │
         │     │  initData HMAC-SHA256 auth     │
         │     └──────────────────────────────┘
```

### Обоснование решений

| Решение | Почему |
|---------|--------|
| Shared Database | 90% операций — CRUD одних данных. REST между всеми сервисами — лишний overhead |
| SQLAlchemy async в боте | ТЗ требует async. Django ORM синхронный — блокирует event loop |
| Django ORM для миграций | Single source of truth. SA-модели зеркалят таблицы без миграций |
| Webhook Django → Bot | Push-уведомления: смена статуса, рассылки, заказы из WebApp |
| `asyncio.create_task` | Для рассылок достаточно. Celery/RabbitMQ — overkill для 1 задачи |
| `shop_core` package | Общие enum'ы и схемы. Нет дублирования между сервисами |
| nginx proxy для /api/ | WebApp и API на одном домене — нет CORS, работает с Telegram Mini App |

---

## Быстрый старт

### Требования

- Docker и Docker Compose
- Telegram Bot Token ([@BotFather](https://t.me/BotFather))

### 1. Клонировать и настроить

```bash
git clone https://github.com/kerz-A/telegram-shop.git
cd telegram-shop
cp .env.example .env
```

Отредактировать `.env`:
- **Обязательно**: `BOT_TOKEN` — токен от BotFather
- **Опционально**: `WEBAPP_URL` — HTTPS URL для Mini App (пусто для localhost)

### 2. Запустить

```bash
docker-compose up --build
```

Дождитесь всех пяти сервисов:
```
db-1              | database system is ready to accept connections
admin_panel-1     | Applying shop.0001_initial... OK
admin_panel-1     | Superuser 'admin' created
bot-1             | Starting bot polling...
webapp-builder-1  | >>> WebApp build complete!
webapp-1          | start worker processes
```

### 3. Первичная настройка

1. **Django Admin** → `http://localhost:8000/admin/` (admin / admin)
2. **Настройки бота** → Добавить → каналы: `[]` → Сохранить
3. Добавить **категории** и **товары** с фотографиями
4. Добавить **FAQ** вопросы
5. В Telegram: `/start` для начала работы

### 4. Mini App (WebApp)

> **Важно:** Telegram Mini App работает **только через HTTPS**. Без HTTPS каталог доступен на `http://localhost:3000` в браузере, но кнопка «🌐 Открыть магазин» в Telegram не появится, а корзина/оформление заказа через Mini App будут недоступны. Бот при этом работает полностью.

**Для продакшена** — разверните проект на сервере с доменом и SSL-сертификатом. Укажите в `.env`:
```
WEBAPP_URL=https://shop.your-domain.com
```

**Для локального тестирования** — используйте HTTPS-туннель:

```bash
# Вариант 1: Cloudflare Tunnel (рекомендуется, без interstitial-страниц)
cloudflared tunnel --url http://localhost:3000

# Вариант 2: ngrok (требует регистрацию)
ngrok http 3000
```

После получения HTTPS URL:
1. В `.env`: `WEBAPP_URL=https://your-tunnel-url.trycloudflare.com`
2. В **@BotFather**: `/setmenubutton` → выбрать бота → отправить URL → текст кнопки
3. Пересоздать контейнер бота: `docker-compose up -d --force-recreate bot`

### 5. Настройка админ-чата

1. Создать группу в Telegram, добавить бота как администратора
2. Узнать `chat_id` группы (через `@getmyid_bot` или из логов бота)
3. Django Admin → **Настройки бота** → `admin_chat_id` → Сохранить

### 6. Настройка Inline Query (FAQ)

В **@BotFather**: `/setinline` → выбрать бота → placeholder: `Поиск FAQ...`

---

## Сервисы

| Сервис | URL | Описание |
|--------|-----|----------|
| Django Admin | `http://localhost:8000/admin/` | Управление магазином |
| WebApp | `http://localhost:3000/` | React каталог (+ proxy /api/ → Django) |
| Bot | Telegram polling | Автоматически |
| PostgreSQL | порт 5432 (внутренний) | Данные |

---

## Структура проекта

```
telegram-shop/
├── docker-compose.yml              # 5 сервисов: db, admin, bot, webapp-builder, webapp
├── .env.example                    # Шаблон переменных окружения
│
├── shop_core/                      # Shared Python Package
│   └── shop_core/
│       ├── enums.py                # OrderStatus, BroadcastStatus (StrEnum)
│       ├── schemas.py              # Pydantic v2 webhook payload
│       └── constants.py            # Пагинация, rate limits, TTL, webhook actions
│
├── bot/                            # Telegram Bot (Aiogram 3)
│   └── app/
│       ├── main.py                 # Polling + aiohttp webhook server
│       ├── config.py               # pydantic-settings
│       ├── db/
│       │   ├── engine.py           # AsyncSession (asyncpg)
│       │   ├── models.py           # SQLAlchemy 2.0 модели (зеркало Django)
│       │   └── repositories/       # Repository pattern
│       ├── middlewares/             # Registration, Subscription, Logging
│       ├── filters/is_admin.py     # Custom filter IsAdmin
│       ├── handlers/               # start, catalog, cart, order, admin_chat, faq, help
│       ├── keyboards/              # CallbackData Factory + inline/reply клавиатуры
│       ├── states/order.py         # FSM: full_name → address → confirmation
│       ├── services/               # notification, broadcast, media
│       └── webhook_server.py       # aiohttp: приём webhook от Django
│
├── admin_panel/                    # Django 5.1 + DRF
│   ├── config/settings.py
│   ├── shop/
│   │   ├── models.py               # 11 моделей (source of truth для всей БД)
│   │   ├── admin.py                # Inlines, actions, Excel export, webhook
│   │   └── migrations/
│   └── api/                        # REST API для WebApp
│       ├── views.py                # Categories, Products, Cart, Orders, Profile
│       ├── serializers.py          # DRF сериализаторы (относительные URL)
│       ├── auth.py                 # Валидация Telegram initData (HMAC-SHA256)
│       └── urls.py
│
└── webapp/                         # React + Vite + TypeScript
    ├── nginx.conf                  # SPA + proxy /api/ и /media/ на Django
    └── src/
        ├── api/client.ts           # Axios + TMA auth + типы
        ├── hooks/useTelegram.ts    # WebApp SDK hook
        ├── context/CartContext.tsx  # Shared cart state
        ├── pages/                  # Catalog, Cart, Checkout
        ├── components/             # ProductCard (с визуальным фидбеком)
        └── theme/global.css        # Telegram themeParams CSS
```

---

## Паттерны Aiogram 3

| Паттерн | Реализация |
|---------|-----------|
| **Router** (7 шт.) | start, catalog, cart, order, admin_chat, faq, help |
| **Middleware** (3 шт.) | Logging, Registration, Subscription |
| **FSM** | Оформление заказа: ФИО → адрес → подтверждение |
| **CallbackData Factory** (6 шт.) | CategoryCB, ProductCB, CartCB, OrderCB, AdminOrderCB, PaginationCB |
| **Custom Filter** | IsAdmin — проверка customer.is_admin |
| **MediaGroup** | Несколько фото товара |
| **Deep Linking** | `t.me/bot?start=product_<id>` |
| **Inline Query** | FAQ поиск + popularity tracking |
| **WebApp** | Кнопка каталога (только при HTTPS) |

---

## WebApp (Mini App)

### Функциональность
- Каталог с картинками, фильтром по категориям и поиском
- Корзина с изменением количества (синхронизация с ботом)
- Визуальный фидбек при добавлении товара: «✓ Добавлено» → «В корзине: N»
- Плавающая кнопка «🛒 Корзина · N шт.»
- Оформление заказа с `Telegram.WebApp.MainButton`
- Навигация через `BackButton`
- Стилизация через `themeParams` (светлая/тёмная тема)
- Защита от двойного оформления заказа

### Авторизация
Telegram передаёт `initData` → WebApp отправляет в header `Authorization: tma <initData>` → Django проверяет HMAC-SHA256 подпись по спецификации Telegram.

### Синхронизация корзины
Одна таблица `CartItem` в PostgreSQL. Бот пишет через SQLAlchemy async, WebApp через Django REST API. Добавил в боте — видно в WebApp. И наоборот.

---

## API Endpoints

| Метод | URL | Auth | Описание |
|-------|-----|:----:|----------|
| GET | `/api/categories/` | — | Список категорий |
| GET | `/api/products/?category=&search=` | — | Товары с фильтрацией |
| GET | `/api/cart/` | TMA | Корзина |
| POST | `/api/cart/` | TMA | Добавить/обновить товар |
| DELETE | `/api/cart/` | TMA | Очистить корзину |
| GET | `/api/orders/` | TMA | Заказы клиента |
| POST | `/api/orders/create/` | TMA | Создать заказ |
| GET | `/api/profile/` | TMA | Профиль |

**TMA** = Telegram Mini App (`Authorization: tma <initData>`, HMAC-SHA256)

---

## UX-решения

- **FSM не перехватывает кнопки меню** — filter `_not_menu` пропускает reply-кнопки
- **Все кнопки сбрасывают FSM** с сообщением «⚠️ Оформление заказа отменено»
- **Защита от пустых заказов** — Django возвращает 400 если корзина пуста
- **Защита от двойного клика** — `useRef` блокирует повторную отправку
- **Рассылки** — только реальным пользователям (с телефоном)
- **Боты не регистрируются** — middleware пропускает `user.is_bot`
- **401 вместо 500** — для неавторизованных запросов к Cart API
- **Уведомления из WebApp** — Django отправляет webhook боту при новом заказе

---

## Переменные окружения

| Переменная | Описание | Обязательна |
|-----------|----------|:-----------:|
| `BOT_TOKEN` | Токен Telegram-бота | ✅ |
| `POSTGRES_DB/USER/PASSWORD` | Параметры БД | ✅ |
| `DJANGO_SECRET_KEY` | Секретный ключ Django | ✅ |
| `WEBAPP_URL` | HTTPS URL Mini App (пусто для localhost) | — |

Бизнес-настройки (каналы подписки, ID админ-чата) управляются через Django-админку **без перезапуска бота**.

---

## Docker

```bash
# Запуск
docker-compose up --build

# Остановка
docker-compose down

# Полная пересборка с очисткой данных
docker-compose down -v
docker-compose up --build

# Перезапуск бота (после изменения .env)
docker-compose up -d --force-recreate bot
```

### Сервисы
- `db` — PostgreSQL 16
- `admin_panel` — Django 5.1 (миграции + collectstatic + superuser при старте)
- `bot` — Aiogram 3 (polling + webhook server на порту 8081)
- `webapp-builder` — Node 20 (npm install + vite build, завершается после сборки)
- `webapp` — nginx (раздаёт SPA + proxy /api/ и /media/ на Django)
