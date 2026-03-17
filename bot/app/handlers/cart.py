import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.app.callbacks.factory import CartCB
from bot.app.db.engine import async_session
from bot.app.db.models import Customer
from bot.app.db.repositories.repo import CartRepo
from bot.app.keyboards.inline import cart_keyboard

logger = logging.getLogger(__name__)

router = Router(name="cart")


def _format_cart_text(items, total) -> str:
    if not items:
        return "🛒 Ваша корзина пуста."

    lines = ["🛒 <b>Ваша корзина:</b>\n"]
    for item in items:
        line_total = item.product.price * item.quantity
        lines.append(f"• {item.product.name} — {item.quantity} × {item.product.price}₽ = {line_total}₽")

    lines.append(f"\n💰 <b>Итого: {total}₽</b>")
    return "\n".join(lines)


# ─── Show cart ──────────────────────────────────────────────────────


@router.message(Command("cart"))
@router.message(F.text == "🛒 Корзина")
async def cmd_cart(message: Message, customer: Customer, state: FSMContext):
    """Show cart contents."""
    current = await state.get_state()
    if current:
        await state.clear()
        await message.answer("⚠️ Оформление заказа отменено.")
    else:
        await state.clear()

    async with async_session() as session:
        repo = CartRepo(session)
        items = await repo.get_items(customer.id)
        total = await repo.get_total(customer.id)

    text = _format_cart_text(items, total)
    if items:
        await message.answer(text, parse_mode="HTML", reply_markup=cart_keyboard(items))
    else:
        await message.answer(text, parse_mode="HTML")


@router.callback_query(CartCB.filter(F.action == "show"))
async def show_cart_callback(callback: CallbackQuery, customer: Customer):
    """Show cart via callback."""
    async with async_session() as session:
        repo = CartRepo(session)
        items = await repo.get_items(customer.id)
        total = await repo.get_total(customer.id)

    text = _format_cart_text(items, total)
    if items:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=cart_keyboard(items))
    else:
        await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


# ─── Add to cart ────────────────────────────────────────────────────


@router.callback_query(CartCB.filter(F.action == "add"))
async def add_to_cart(callback: CallbackQuery, callback_data: CartCB, customer: Customer):
    """Add product to cart."""
    async with async_session() as session:
        repo = CartRepo(session)
        await repo.add_or_update(customer.id, callback_data.product_id, delta=1)

    await callback.answer("✅ Добавлено в корзину!", show_alert=False)


# ─── Quantity controls ──────────────────────────────────────────────


@router.callback_query(CartCB.filter(F.action == "plus"))
async def cart_plus(callback: CallbackQuery, callback_data: CartCB, customer: Customer):
    async with async_session() as session:
        repo = CartRepo(session)
        await repo.add_or_update(customer.id, callback_data.product_id, delta=1)
        items = await repo.get_items(customer.id)
        total = await repo.get_total(customer.id)

    text = _format_cart_text(items, total)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=cart_keyboard(items))
    await callback.answer()


@router.callback_query(CartCB.filter(F.action == "minus"))
async def cart_minus(callback: CallbackQuery, callback_data: CartCB, customer: Customer):
    async with async_session() as session:
        repo = CartRepo(session)
        # Get current quantity
        items = await repo.get_items(customer.id)
        current_item = next(
            (i for i in items if i.product_id == callback_data.product_id), None
        )

        if current_item and current_item.quantity <= 1:
            await repo.remove_item(customer.id, callback_data.product_id)
        else:
            await repo.add_or_update(customer.id, callback_data.product_id, delta=-1)

        items = await repo.get_items(customer.id)
        total = await repo.get_total(customer.id)

    text = _format_cart_text(items, total)
    if items:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=cart_keyboard(items))
    else:
        await callback.message.edit_text("🛒 Ваша корзина пуста.", parse_mode="HTML")
    await callback.answer()


# ─── Remove item ────────────────────────────────────────────────────


@router.callback_query(CartCB.filter(F.action == "remove"))
async def cart_remove(callback: CallbackQuery, callback_data: CartCB, customer: Customer):
    async with async_session() as session:
        repo = CartRepo(session)
        await repo.remove_item(customer.id, callback_data.product_id)
        items = await repo.get_items(customer.id)
        total = await repo.get_total(customer.id)

    text = _format_cart_text(items, total)
    if items:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=cart_keyboard(items))
    else:
        await callback.message.edit_text("🛒 Ваша корзина пуста.", parse_mode="HTML")
    await callback.answer("🗑 Товар удалён")


# ─── Clear cart ─────────────────────────────────────────────────────


@router.callback_query(CartCB.filter(F.action == "clear"))
async def cart_clear(callback: CallbackQuery, customer: Customer):
    async with async_session() as session:
        repo = CartRepo(session)
        await repo.clear(customer.id)

    await callback.message.edit_text("🛒 Корзина очищена.", parse_mode="HTML")
    await callback.answer("🗑 Корзина очищена")
