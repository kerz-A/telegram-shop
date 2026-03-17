# 🛒 Telegram Shop Bot

Интернет-магазин из трёх независимых сервисов: **Telegram-бот** (Aiogram 3), **Django-админка** (DRF) и **React WebApp** (Vite + TypeScript).

Весь проект поднимается **одной командой**: `docker-compose up --build`

---

## Архитектура

```
┌─────────────────┐    Shared DB     ┌──────────────────┐
│  Telegram Bot    │◄───────────────►│  Django Admin     │
│  (Aiogram 3)    │   (PostgreSQL)   │  + REST API (DRF) │
│  async polling   │                  │                    │
└────────┬────────┘                  └────────┬───────────┘
         │                                     │
         │◄─── Webhook (HTTP POST) ────────────┘
         │     (order status, broadcasts)
         │
         │                              ┌──────────────────┐
         │                              │  React WebApp     │
         │                              │  (Vite + TS)      │
         │                              │  nginx → :3000    │
         │                              └────────┬─────────┘
         │              REST API (DRF)           │
         └───────────────────────────────────────┘
```

### Обоснование выбора

**Shared Database (PostgreSQL)** — все три сервиса работают с одной БД. Django ORM определяет модели и миграции (single source of truth). Бот использует SQLAlchemy 2.0 async + asyncpg для неблокирующего доступа. WebApp обращается к БД через Django REST Framework API.

**Почему не REST API между всеми сервисами?** Оверхед. 90% взаимодействий — чтение/запись в одну базу. REST API оправдан только для push-уведомлений (Django → Bot), реализованных через внутренний webhook.

**Почему не Message Broker (Celery/RabbitMQ)?** Единственная фоновая задача — рассылки. Решена через `asyncio.create_task` с rate limiting. Для данного масштаба broker — избыточная инфраструктура.

**Shared Python Package (`shop_core`)** — общие Pydantic-схемы, Enum'ы статусов и константы. Устанавливается как editable package в бот и Django.

**Webhook для нотификаций** — Django при смене статуса заказа или запуске рассылки делает HTTP POST на внутренний aiohttp-сервер бота (порт 8081).

---

## Быстрый старт

### Требования

- Docker и Docker Compose
- Telegram Bot Token (от [@BotFather](https://t.me/BotFather))

### Запуск

```bash
# 1. Клонировать
git clone https://github.com/kerz-A/telegram-shop.git
cd telegram-shop

# 2. Создать .env
cp .env.example .env
# Заполнить BOT_TOKEN (обязательно)

# 3. Запустить
docker-compose up --build

# Сервисы:
# Django Admin:  http://localhost:8000/admin/ (admin / admin)
# WebApp:        http://localhost:3000/
# Bot:           Telegram polling (автоматически)
```

### Первичная настройка

1. Django Admin → **Настройки бота** → добавить запись (каналы: `[]`)
2. Добавить категории и товары с фотографиями
3. Добавить FAQ вопросы
4. В Telegram: `/start` для начала работы с ботом

---

## Структура проекта

```
telegram-shop/
├── docker-compose.yml
├── .env.example
├── shop_core/                      # Shared Python Package
│   └── shop_core/
│       ├── enums.py                # OrderStatus, BroadcastStatus
│       ├── schemas.py              # Pydantic v2 webhook payload
│       └── constants.py            # Пагинация, rate limits, TTL
│
├── bot/                            # Telegram Bot (Aiogram 3)
│   └── app/
│       ├── main.py                 # Polling + aiohttp webhook server
│       ├── config.py               # pydantic-settings
│       ├── db/
│       │   ├── engine.py           # AsyncSession (asyncpg)
│       │   ├── models.py           # SQLAlchemy 2.0 модели
│       │   └── repositories/       # Repository pattern
│       ├── middlewares/             # Registration, Subscription, Logging
│       ├── filters/is_admin.py     # Custom filter IsAdmin
│       ├── handlers/               # start, catalog, cart, order, admin_chat, faq, help
│       ├── keyboards/              # CallbackData Factory + inline/reply клавиатуры
│       ├── callbacks/factory.py    # 6 CallbackData классов
│       ├── states/order.py         # FSM: full_name → address → confirmation
│       ├── services/               # notification, broadcast, media
│       └── webhook_server.py       # aiohttp приём webhook от Django
│
├── admin_panel/                    # Django 5.1 + DRF
│   ├── config/settings.py
│   ├── shop/
│   │   ├── models.py               # 11 моделей (source of truth)
│   │   ├── admin.py                # Inlines, actions, annotated fields
│   │   └── migrations/
│   └── api/                        # REST API для WebApp
│       ├── views.py
│       ├── serializers.py
│       └── auth.py                 # Валидация Telegram initData (HMAC-SHA256)
│
└── webapp/                         # React + Vite + TypeScript
    └── src/
        ├── api/client.ts           # Axios + TMA auth
        ├── hooks/useTelegram.ts    # WebApp SDK hook
        ├── context/CartContext.tsx  # Shared cart state
        ├── pages/                  # Catalog, Cart, Checkout
        └── theme/global.css        # Telegram themeParams CSS
```

---

## Паттерны Aiogram 3

| Паттерн | Реализация |
|---------|-----------|
| **Router** | Каждый handler-модуль — отдельный Router |
| **Middleware** (3 шт.) | Registration, Subscription, Logging |
| **FSM** | Оформление заказа: ФИО → адрес → подтверждение |
| **CallbackData Factory** | CategoryCB, ProductCB, CartCB, OrderCB, AdminOrderCB, PaginationCB |
| **Custom Filters** | IsAdmin — проверка customer.is_admin |
| **MediaGroup** | Несколько фото товара |
| **Deep Linking** | `t.me/bot?start=product_<id>` |
| **Inline Query** | FAQ поиск + popularity tracking |
| **WebApp** | Кнопка каталога (только HTTPS) |

---

## Асинхронность

- **SQLAlchemy 2.0 async + asyncpg** — ни одного синхронного вызова к БД из бота
- **Рассылки** — `asyncio.create_task` с rate limiting (25 msg/sec)
- **Webhook-сервер** — aiohttp параллельно с polling
- **Кеш настроек** — in-memory TTL 60 секунд

---

## UX-решения

- **Нет тупиков** — из любого экрана каталога есть возврат
- **FSM не перехватывает кнопки меню** — filter `_not_menu` пропускает reply-кнопки
- **Все кнопки сбрасывают FSM** с сообщением «⚠️ Оформление заказа отменено»
- **Deep linking с невалидными ID** — понятные сообщения об ошибках
- **Рассылки** — только реальным пользователям (с телефоном)
- **Боты не регистрируются** — middleware пропускает `user.is_bot`

---

## API Endpoints

| Метод | URL | Auth |
|-------|-----|:----:|
| GET | `/api/categories/` | — |
| GET | `/api/products/?category=&search=` | — |
| GET | `/api/products/<id>/` | — |
| GET | `/api/cart/` | TMA |
| POST | `/api/cart/` | TMA |
| DELETE | `/api/cart/` | TMA |
| GET | `/api/orders/` | TMA |
| POST | `/api/orders/create/` | TMA |
| GET | `/api/profile/` | TMA |

**TMA** = Telegram Mini App (`Authorization: tma <initData>`, HMAC-SHA256)

---

## Переменные окружения

| Переменная | Описание | Обязательна |
|-----------|----------|:-----------:|
| `BOT_TOKEN` | Токен Telegram-бота | ✅ |
| `POSTGRES_DB/USER/PASSWORD` | Параметры БД | ✅ |
| `DJANGO_SECRET_KEY` | Секретный ключ Django | ✅ |
| `WEBAPP_URL` | HTTPS URL WebApp (пусто для localhost) | — |

**Бизнес-настройки** (каналы подписки, ID админ-чата) управляются через Django-админку без перезапуска бота.
