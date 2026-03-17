# 🛒 Telegram Shop Bot

Интернет-магазин из трёх независимых сервисов: Telegram-бот, Django-админка и React WebApp.

## Архитектура

### Схема взаимодействия

```
┌─────────────┐     Shared DB      ┌──────────────────┐
│  Telegram    │◄──────────────────►│  Django Admin     │
│  Bot         │    (PostgreSQL)    │  + REST API       │
│  (Aiogram 3) │                    │  (DRF)            │
└──────┬───────┘                    └────────┬──────────┘
       │                                     │
       │◄──── Webhook (HTTP POST) ───────────┘
       │      (order status, broadcasts)
       │                                ┌──────────────┐
       │                                │  React       │
       │                                │  WebApp      │
       │                                │  (Vite + TS) │
       │                                └──────┬───────┘
       │                                       │
       │              REST API                 │
       └───────────────────────────────────────┘
                  (через Django)
```

### Обоснование выбора архитектуры

**Shared Database (PostgreSQL)** — все три сервиса работают с одной базой данных. Django ORM определяет модели и миграции (single source of truth). Бот использует SQLAlchemy 2.0 async с asyncpg для неблокирующего доступа. WebApp обращается к БД через Django REST API.

**Почему не REST API между всеми сервисами?** Оверхед. 90% взаимодействий — это чтение/запись в одну базу. REST API оправдан только для push-уведомлений (Django → Bot), что реализовано через внутренний webhook.

**Почему не Message Broker (Celery/RabbitMQ)?** Единственная фоновая задача — рассылки. Она решена через `asyncio.create_task` в боте. Для проекта данного масштаба broker — избыточная инфраструктура.

**Shared Python Package (`shop_core`)** — общие Pydantic-схемы, Enum'ы статусов и константы. Устанавливается как editable package в бот и Django, исключая рассинхронизацию типов.

**Webhook для нотификаций** — когда Django меняет статус заказа или запускает рассылку, он делает HTTP POST на внутренний aiohttp-сервер бота. Бот обрабатывает запрос и отправляет сообщения пользователям.

## Быстрый старт

### Требования

- Docker и Docker Compose
- Telegram Bot Token (от @BotFather)

### Запуск

```bash
# 1. Клонировать репозиторий
git clone <repo-url>
cd telegram-shop

# 2. Создать .env файл
cp .env.example .env
# Заполнить BOT_TOKEN и другие параметры

# 3. Запустить
docker-compose up --build

# Сервисы:
# - Django Admin:  http://localhost:8000/admin/
# - WebApp:        http://localhost:3000/
# - Bot:           polling (автоматически)
```

### Первичная настройка

1. Откройте Django Admin: `http://localhost:8000/admin/` (admin / admin)
2. Перейдите в **Настройки бота** и укажите:
   - Каналы для обязательной подписки (формат: `["@channel_name"]`)
   - ID админ-чата (ID Telegram-группы для уведомлений)
3. Добавьте категории и товары через админку
4. Добавьте FAQ вопросы
5. Начните взаимодействие с ботом в Telegram

## Структура проекта

```
telegram-shop/
├── docker-compose.yml          # Оркестрация всех сервисов
├── .env.example                # Шаблон переменных окружения
│
├── shop_core/                  # Shared Python Package
│   ├── pyproject.toml
│   └── shop_core/
│       ├── enums.py            # OrderStatus, BroadcastStatus
│       ├── schemas.py          # Pydantic-модели для webhook
│       └── constants.py        # Общие константы
│
├── bot/                        # Telegram Bot (Aiogram 3)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # Entrypoint: бот + webhook-сервер
│       ├── config.py           # Настройки из env
│       ├── db/
│       │   ├── engine.py       # Async SQLAlchemy engine
│       │   ├── models.py       # SA-модели (зеркало Django таблиц)
│       │   └── repositories/   # Repository pattern (все запросы)
│       ├── middlewares/
│       │   ├── registration.py # Авторегистрация + инъекция customer
│       │   ├── subscription.py # Проверка подписки на каналы
│       │   └── logging.py      # Логирование всех апдейтов
│       ├── filters/
│       │   └── is_admin.py     # Кастомный фильтр IsAdmin
│       ├── handlers/
│       │   ├── start.py        # /start + deep linking + контакт
│       │   ├── catalog.py      # Каталог с пагинацией
│       │   ├── cart.py         # Корзина (CRUD)
│       │   ├── order.py        # FSM оформления заказа
│       │   ├── admin_chat.py   # Админ-чат + inline-кнопки статусов
│       │   ├── faq.py          # Inline Query FAQ
│       │   └── help.py         # /help
│       ├── keyboards/
│       │   ├── inline.py       # CallbackData Factory + клавиатуры
│       │   └── reply.py        # Reply-клавиатуры + WebApp кнопка
│       ├── callbacks/
│       │   └── factory.py      # Все CallbackData классы
│       ├── states/
│       │   └── order.py        # FSM states
│       ├── services/
│       │   ├── notification.py # Уведомления пользователям
│       │   ├── broadcast.py    # Фоновые рассылки
│       │   └── media.py        # MediaGroup builder
│       └── webhook_server.py   # aiohttp для приёма webhook
│
├── admin_panel/                # Django Admin + REST API
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── config/
│   │   ├── settings.py         # Настройки Django
│   │   └── urls.py
│   ├── shop/                   # Основное приложение
│   │   ├── models.py           # ВСЕ модели (source of truth)
│   │   ├── admin.py            # Кастомная админка
│   │   ├── signals.py
│   │   └── management/commands/
│   │       └── ensure_superuser.py
│   └── api/                    # DRF API для WebApp
│       ├── views.py
│       ├── serializers.py
│       ├── urls.py
│       └── auth.py             # Валидация Telegram initData
│
└── webapp/                     # React WebApp (Vite + TypeScript)
    ├── Dockerfile
    ├── package.json
    ├── nginx.conf
    └── src/
        ├── api/client.ts       # Axios + типы + API методы
        ├── hooks/useTelegram.ts # Хук для Telegram WebApp SDK
        ├── context/CartContext.tsx
        ├── pages/
        │   ├── Catalog.tsx     # Каталог с поиском и фильтрами
        │   ├── Cart.tsx        # Корзина
        │   └── Checkout.tsx    # Оформление заказа
        ├── components/
        │   └── ProductCard.tsx
        ├── utils/telegram.ts   # SDK типы и утилиты
        └── theme/global.css    # Стилизация через themeParams
```

## Переменные окружения

| Переменная | Описание | Пример |
|---|---|---|
| `POSTGRES_DB` | Имя базы данных | `shop_db` |
| `POSTGRES_USER` | Пользователь БД | `shop_user` |
| `POSTGRES_PASSWORD` | Пароль БД | `strong_password` |
| `BOT_TOKEN` | Токен Telegram-бота | `123456:ABC...` |
| `DJANGO_SECRET_KEY` | Секретный ключ Django | `random-string` |
| `WEBAPP_URL` | URL WebApp (HTTPS) | `https://example.com/webapp` |
| `VITE_API_BASE_URL` | URL API для WebApp | `https://example.com/api` |

**Бизнес-настройки** (каналы для подписки, ID админ-чата) управляются через Django-админку, а не через `.env`.

## Ключевые паттерны Aiogram 3

| Паттерн | Где используется |
|---|---|
| **Router** | Каждый handler-модуль — отдельный Router |
| **Middleware** | Registration, Subscription, Logging |
| **FSM** | Оформление заказа (ФИО → адрес → подтверждение) |
| **CallbackData Factory** | CategoryCB, ProductCB, CartCB, OrderCB, AdminOrderCB |
| **Custom Filters** | IsAdmin |
| **MediaGroup** | Фото товаров |
| **Deep Linking** | `t.me/bot?start=product_<id>` |
| **Inline Query** | FAQ поиск |
| **WebApp** | Кнопка открытия каталога |

## Асинхронность

- Бот использует **SQLAlchemy 2.0 async** + **asyncpg** — ни одного синхронного вызова к БД
- Рассылки выполняются через `asyncio.create_task` — не блокируют event loop
- Webhook-сервер на **aiohttp** работает параллельно с polling

## API Endpoints (для WebApp)

| Метод | URL | Описание | Авторизация |
|---|---|---|---|
| GET | `/api/categories/` | Список категорий | — |
| GET | `/api/products/` | Товары (фильтр: category, search) | — |
| GET | `/api/products/<id>/` | Детали товара | — |
| GET | `/api/cart/` | Содержимое корзины | TMA |
| POST | `/api/cart/` | Добавить/обновить товар | TMA |
| DELETE | `/api/cart/` | Очистить корзину | TMA |
| GET | `/api/orders/` | Список заказов | TMA |
| POST | `/api/orders/create/` | Создать заказ | TMA |
| GET | `/api/profile/` | Профиль клиента | TMA |

**TMA** = Telegram Mini App авторизация (Header: `Authorization: tma <initData>`)
