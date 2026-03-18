import logging

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.app.callbacks.factory import AdminOrderCB
from bot.app.db.engine import async_session
from bot.app.db.repositories.repo import OrderRepo
from bot.app.filters.is_admin import IsAdmin
from bot.app.keyboards.inline import admin_order_keyboard
from bot.app.services.notification import notify_order_status
from shop_core.enums import OrderStatus

logger = logging.getLogger(__name__)

router = Router(name="admin_chat")


# ─── Admin changes order status from inline buttons ─────────────────


@router.callback_query(AdminOrderCB.filter())
async def admin_change_status(
    callback: CallbackQuery,
    callback_data: AdminOrderCB,
    bot: Bot,
):
    """Admin changes order status from admin chat inline buttons."""
    order_id = callback_data.order_id
    new_status = OrderStatus(callback_data.action)

    async with async_session() as session:
        repo = OrderRepo(session)
        order = await repo.update_status(order_id, new_status)

    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return

    # Notify user
    await notify_order_status(
        bot=bot,
        telegram_id=order.customer.telegram_id,
        order_id=order_id,
        new_status=new_status,
    )

    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ Статус изменён: {new_status.label}",
        reply_markup=admin_order_keyboard(order_id),
    )
    await callback.answer(f"Статус: {new_status.label}")


# ─── Active orders command (for admin chat) ─────────────────────────


@router.message(Command("active_orders"), IsAdmin())
async def active_orders(message: Message):
    """Show all active orders."""
    async with async_session() as session:
        repo = OrderRepo(session)
        orders = await repo.get_active_orders()

    if not orders:
        await message.answer("📋 Нет активных заказов.")
        return

    lines = ["📋 <b>Активные заказы:</b>\n"]
    for order in orders:
        status_label = OrderStatus(order.status).label
        customer_name = order.customer.first_name if order.customer else "—"
        lines.append(
            f"#{order.id} | {customer_name} | {status_label} | {order.total}₽"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")
