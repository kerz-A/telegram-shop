import logging

from aiogram import Bot

from shop_core.enums import OrderStatus

logger = logging.getLogger(__name__)


async def notify_order_status(
    bot: Bot,
    telegram_id: int,
    order_id: int,
    new_status: OrderStatus,
    message: str | None = None,
) -> bool:
    """Send order status notification to user."""
    text = (
        f"📦 <b>Заказ #{order_id}</b>\n\n"
        f"Новый статус: {new_status.label}\n"
    )
    if message:
        text += f"\n💬 {message}"

    try:
        await bot.send_message(chat_id=telegram_id, text=text, parse_mode="HTML")
        return True
    except Exception as e:
        logger.error("Failed to notify user %s about order %s: %s", telegram_id, order_id, e)
        return False


async def send_order_to_admin_chat(
    bot: Bot,
    admin_chat_id: int,
    order_id: int,
    customer_name: str,
    customer_phone: str,
    address: str,
    total,
    items_text: str,
    keyboard=None,
) -> bool:
    """Send new order notification to admin chat."""
    text = (
        f"🆕 <b>Новый заказ #{order_id}</b>\n\n"
        f"👤 {customer_name}\n"
        f"📱 {customer_phone}\n"
        f"📍 {address}\n\n"
        f"📋 <b>Позиции:</b>\n{items_text}\n\n"
        f"💰 <b>Итого: {total}₽</b>"
    )
    try:
        await bot.send_message(
            chat_id=admin_chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return True
    except Exception as e:
        logger.error("Failed to send order to admin chat: %s", e)
        return False
