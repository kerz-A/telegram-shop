from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    WebAppInfo,
)


def contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Поделиться контактом", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def main_menu_keyboard(webapp_url: str | None = None) -> ReplyKeyboardMarkup:
    rows = [
        [
            KeyboardButton(text="🛍 Каталог"),
            KeyboardButton(text="🛒 Корзина"),
        ],
        [
            KeyboardButton(text="📋 Мои заказы"),
            KeyboardButton(text="❓ Помощь"),
        ],
    ]
    # Only show WebApp button if URL is real HTTPS (not placeholder)
    if (
        webapp_url
        and webapp_url.startswith("https://")
        and "your-domain" not in webapp_url
    ):
        rows.append([
            KeyboardButton(
                text="🌐 Открыть магазин",
                web_app=WebAppInfo(url=webapp_url),
            )
        ])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


remove_keyboard = ReplyKeyboardRemove()
