import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.app.callbacks.factory import CategoryCB, PaginationCB, ProductCB
from bot.app.config import settings
from bot.app.db.engine import async_session
from bot.app.db.models import Customer
from bot.app.db.repositories.repo import CategoryRepo, ProductRepo
from bot.app.keyboards.inline import (
    categories_keyboard,
    product_card_keyboard,
    products_keyboard,
    webapp_catalog_button,
)
from bot.app.services.media import build_product_media_group
from shop_core.constants import PRODUCTS_PER_PAGE

logger = logging.getLogger(__name__)

router = Router(name="catalog")


# ─── /catalog command and text button ───────────────────────────────


@router.message(Command("catalog"))
@router.message(F.text == "🛍 Каталог")
async def cmd_catalog(message: Message, state: FSMContext):
    """Show root categories."""
    current = await state.get_state()
    if current:
        await state.clear()
        await message.answer("⚠️ Оформление заказа отменено.")

    async with async_session() as session:
        repo = CategoryRepo(session)
        categories = await repo.get_root_categories()

    if not categories:
        await message.answer("😔 Каталог пока пуст.")
        return

    await message.answer(
        "📂 <b>Каталог</b>\n\nВыберите категорию:",
        parse_mode="HTML",
        reply_markup=categories_keyboard(categories),
    )

    # Also offer WebApp button (only for valid HTTPS URLs)
    if settings.webapp_url and settings.webapp_url.startswith("https://"):
        await message.answer(
            "Или откройте полный каталог:",
            reply_markup=webapp_catalog_button(settings.webapp_url),
        )


# ─── Category navigation ───────────────────────────────────────────


@router.callback_query(CategoryCB.filter(F.action == "show"))
async def show_category(callback: CallbackQuery, callback_data: CategoryCB):
    """Show subcategories or products for a category."""
    category_id = callback_data.id

    async with async_session() as session:
        cat_repo = CategoryRepo(session)
        subcategories = await cat_repo.get_subcategories(category_id)

        if subcategories:
            await callback.message.edit_text(
                "📂 Выберите подкатегорию:",
                reply_markup=categories_keyboard(
                    subcategories, parent_id=category_id
                ),
            )
        else:
            # Show products
            prod_repo = ProductRepo(session)
            products, total = await prod_repo.get_by_category(category_id)

            if not products:
                await callback.answer("В этой категории пока нет товаров")
                return

            category = await cat_repo.get_by_id(category_id)
            cat_name = category.name if category else "Товары"

            await callback.message.edit_text(
                f"📦 <b>{cat_name}</b> ({total} шт.)\n\nВыберите товар:",
                parse_mode="HTML",
                reply_markup=products_keyboard(products, category_id, page=0, total=total),
            )

    await callback.answer()


@router.callback_query(CategoryCB.filter(F.action == "back"))
async def back_to_categories(callback: CallbackQuery, callback_data: CategoryCB):
    """Go back to parent categories or root."""
    category_id = callback_data.id

    async with async_session() as session:
        cat_repo = CategoryRepo(session)

        if category_id == 0:
            # Root
            categories = await cat_repo.get_root_categories()
            await callback.message.edit_text(
                "📂 <b>Каталог</b>\n\nВыберите категорию:",
                parse_mode="HTML",
                reply_markup=categories_keyboard(categories),
            )
        else:
            category = await cat_repo.get_by_id(category_id)
            parent_id = category.parent_id if category else None

            if parent_id:
                subcategories = await cat_repo.get_subcategories(parent_id)
                await callback.message.edit_text(
                    "📂 Выберите подкатегорию:",
                    reply_markup=categories_keyboard(subcategories, parent_id=parent_id),
                )
            else:
                categories = await cat_repo.get_root_categories()
                await callback.message.edit_text(
                    "📂 <b>Каталог</b>\n\nВыберите категорию:",
                    parse_mode="HTML",
                    reply_markup=categories_keyboard(categories),
                )

    await callback.answer()


# ─── Pagination ─────────────────────────────────────────────────────


@router.callback_query(PaginationCB.filter(F.target == "products"))
async def paginate_products(callback: CallbackQuery, callback_data: PaginationCB):
    """Handle product pagination."""
    category_id = callback_data.id
    page = callback_data.page

    async with async_session() as session:
        prod_repo = ProductRepo(session)
        offset = page * PRODUCTS_PER_PAGE
        products, total = await prod_repo.get_by_category(
            category_id, offset=offset, limit=PRODUCTS_PER_PAGE
        )

        cat_repo = CategoryRepo(session)
        category = await cat_repo.get_by_id(category_id)
        cat_name = category.name if category else "Товары"

    await callback.message.edit_text(
        f"📦 <b>{cat_name}</b> ({total} шт.) — стр. {page + 1}\n\nВыберите товар:",
        parse_mode="HTML",
        reply_markup=products_keyboard(products, category_id, page=page, total=total),
    )
    await callback.answer()


@router.callback_query(PaginationCB.filter(F.target == "categories"))
async def paginate_categories(callback: CallbackQuery, callback_data: PaginationCB):
    """Handle category pagination."""
    parent_id = callback_data.id or None
    page = callback_data.page

    async with async_session() as session:
        cat_repo = CategoryRepo(session)
        if parent_id:
            categories = await cat_repo.get_subcategories(parent_id)
        else:
            categories = await cat_repo.get_root_categories()

    await callback.message.edit_text(
        "📂 Выберите категорию:",
        reply_markup=categories_keyboard(categories, page=page, parent_id=parent_id),
    )
    await callback.answer()


# ─── Product card ───────────────────────────────────────────────────


@router.callback_query(ProductCB.filter(F.action == "show"))
async def show_product(callback: CallbackQuery, callback_data: ProductCB):
    """Show single product card with photos."""
    product_id = callback_data.id
    category_id = callback_data.cat_id

    async with async_session() as session:
        repo = ProductRepo(session)
        product = await repo.get_by_id(product_id)

    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return

    # Send media group if images exist
    media_group = build_product_media_group(product)
    if media_group:
        await callback.message.answer_media_group(media=media_group)

    text = (
        f"<b>{product.name}</b>\n\n"
        f"{product.description}\n\n"
        f"💰 <b>{product.price}₽</b>"
    )
    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=product_card_keyboard(product, category_id),
    )
    await callback.answer()


@router.callback_query(ProductCB.filter(F.action == "list"))
async def back_to_product_list(callback: CallbackQuery, callback_data: ProductCB):
    """Go back to product list for a category."""
    category_id = callback_data.cat_id

    async with async_session() as session:
        prod_repo = ProductRepo(session)
        products, total = await prod_repo.get_by_category(category_id)

        cat_repo = CategoryRepo(session)
        category = await cat_repo.get_by_id(category_id)
        cat_name = category.name if category else "Товары"

    await callback.message.edit_text(
        f"📦 <b>{cat_name}</b> ({total} шт.)\n\nВыберите товар:",
        parse_mode="HTML",
        reply_markup=products_keyboard(products, category_id, page=0, total=total),
    )
    await callback.answer()


# noop callback
@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    await callback.answer()
