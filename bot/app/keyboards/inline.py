from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.app.callbacks.factory import (
    AdminOrderCB,
    CartCB,
    CategoryCB,
    OrderCB,
    PaginationCB,
    ProductCB,
)
from bot.app.db.models import CartItem, Category, Order, Product
from shop_core.constants import CATEGORIES_PER_PAGE, PRODUCTS_PER_PAGE
from shop_core.enums import OrderStatus


# ─── Catalog ────────────────────────────────────────────────────────


def categories_keyboard(
    categories: list[Category],
    page: int = 0,
    parent_id: int | None = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    start = page * CATEGORIES_PER_PAGE
    end = start + CATEGORIES_PER_PAGE
    page_items = categories[start:end]

    for cat in page_items:
        builder.button(
            text=f"📁 {cat.name}",
            callback_data=CategoryCB(action="show", id=cat.id),
        )
    builder.adjust(2)

    # Pagination
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=PaginationCB(
                    target="categories", id=parent_id or 0, page=page - 1
                ).pack(),
            )
        )
    if end < len(categories):
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперёд ▶️",
                callback_data=PaginationCB(
                    target="categories", id=parent_id or 0, page=page + 1
                ).pack(),
            )
        )
    if nav_buttons:
        builder.row(*nav_buttons)

    # Back to parent
    if parent_id:
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data=CategoryCB(action="back", id=parent_id).pack(),
            )
        )

    return builder.as_markup()


def products_keyboard(
    products: list[Product],
    category_id: int,
    page: int = 0,
    total: int = 0,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for product in products:
        builder.button(
            text=f"{product.name} — {product.price}₽",
            callback_data=ProductCB(
                action="show", id=product.id, cat_id=category_id
            ),
        )
    builder.adjust(1)

    # Pagination
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=PaginationCB(
                    target="products", id=category_id, page=page - 1
                ).pack(),
            )
        )
    if (page + 1) * PRODUCTS_PER_PAGE < total:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперёд ▶️",
                callback_data=PaginationCB(
                    target="products", id=category_id, page=page + 1
                ).pack(),
            )
        )
    if nav_buttons:
        builder.row(*nav_buttons)

    # Back to category
    builder.row(
        InlineKeyboardButton(
            text="🔙 К категориям",
            callback_data=CategoryCB(action="back", id=0).pack(),
        )
    )

    return builder.as_markup()


def product_card_keyboard(
    product: Product, category_id: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🛒 В корзину",
        callback_data=CartCB(action="add", product_id=product.id),
    )
    builder.button(
        text="🔙 К товарам",
        callback_data=ProductCB(action="list", cat_id=category_id),
    )
    builder.adjust(1)
    return builder.as_markup()


def webapp_catalog_button(webapp_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 Открыть каталог",
                    web_app=WebAppInfo(url=webapp_url),
                )
            ]
        ]
    )


# ─── Cart ───────────────────────────────────────────────────────────


def cart_keyboard(items: list[CartItem]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for item in items:
        # Product name row
        builder.row(
            InlineKeyboardButton(
                text=f"📦 {item.product.name} ({item.product.price}₽)",
                callback_data="noop",
            )
        )
        # Quantity controls row
        builder.row(
            InlineKeyboardButton(
                text="➖",
                callback_data=CartCB(action="minus", product_id=item.product_id).pack(),
            ),
            InlineKeyboardButton(
                text=f"{item.quantity} шт.",
                callback_data="noop",
            ),
            InlineKeyboardButton(
                text="➕",
                callback_data=CartCB(action="plus", product_id=item.product_id).pack(),
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=CartCB(action="remove", product_id=item.product_id).pack(),
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text="🗑 Очистить корзину",
            callback_data=CartCB(action="clear").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="✅ Оформить заказ",
            callback_data=OrderCB(action="checkout").pack(),
        )
    )
    return builder.as_markup()


# ─── Order ──────────────────────────────────────────────────────────


def order_confirm_keyboard(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Подтвердить заказ",
        callback_data=OrderCB(action="confirm", order_id=order_id),
    )
    builder.button(
        text="❌ Отменить",
        callback_data=OrderCB(action="cancel", order_id=order_id),
    )
    builder.adjust(1)
    return builder.as_markup()


def order_payment_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Я оплатил(а)",
                    callback_data=OrderCB(action="paid", order_id=order_id).pack(),
                )
            ]
        ]
    )


# ─── Admin Chat ─────────────────────────────────────────────────────


def admin_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    statuses = [
        ("✅ Оплачен", OrderStatus.PAID),
        ("📦 Собирается", OrderStatus.PROCESSING),
        ("🚚 Отправлен", OrderStatus.SHIPPED),
        ("🎉 Доставлен", OrderStatus.DELIVERED),
        ("❌ Отменён", OrderStatus.CANCELLED),
    ]
    for label, status in statuses:
        builder.button(
            text=label,
            callback_data=AdminOrderCB(action=status.value, order_id=order_id),
        )
    builder.adjust(2)
    return builder.as_markup()
