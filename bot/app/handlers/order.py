import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.app.callbacks.factory import OrderCB
from bot.app.db.engine import async_session
from bot.app.db.models import Customer
from bot.app.db.repositories.repo import CartRepo, OrderRepo, SettingsRepo
from bot.app.keyboards.inline import order_confirm_keyboard, order_payment_keyboard, admin_order_keyboard
from bot.app.services.notification import send_order_to_admin_chat
from bot.app.states.order import OrderFSM
from shop_core.enums import OrderStatus

logger = logging.getLogger(__name__)

# Menu button texts — FSM handlers must NOT capture these
MENU_BUTTONS = {"🛍 Каталог", "🛒 Корзина", "📋 Мои заказы", "❓ Помощь"}

# Filter: text exists AND is NOT a menu button AND is NOT a command
_not_menu = F.text & ~F.text.in_(MENU_BUTTONS) & ~F.text.startswith("/")

router = Router(name="order")


# ─── Start order flow ───────────────────────────────────────────────


@router.callback_query(OrderCB.filter(F.action == "checkout"))
async def start_order(callback: CallbackQuery, state: FSMContext, customer: Customer):
    """Begin FSM: ask for full name."""
    # Check cart is not empty
    async with async_session() as session:
        cart_repo = CartRepo(session)
        items = await cart_repo.get_items(customer.id)

    if not items:
        await callback.answer("Корзина пуста!", show_alert=True)
        return

    await state.set_state(OrderFSM.full_name)
    await callback.message.answer(
        "📝 <b>Оформление заказа</b>\n\n"
        f"📱 Телефон: {customer.phone}\n\n"
        "Введите ваше <b>ФИО</b>:",
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Step 1: Full name ──────────────────────────────────────────────


@router.message(OrderFSM.full_name, _not_menu)
async def process_full_name(message: Message, state: FSMContext):
    if len(message.text) < 2:
        await message.answer("❌ Пожалуйста, введите полное ФИО.")
        return

    await state.update_data(full_name=message.text)
    await state.set_state(OrderFSM.address)
    await message.answer(
        "📍 Введите <b>адрес доставки</b>:",
        parse_mode="HTML",
    )


# ─── Step 2: Address ────────────────────────────────────────────────


@router.message(OrderFSM.address, _not_menu)
async def process_address(message: Message, state: FSMContext, customer: Customer):
    if len(message.text) < 5:
        await message.answer("❌ Пожалуйста, введите полный адрес.")
        return

    await state.update_data(address=message.text)
    await state.set_state(OrderFSM.confirmation)

    data = await state.get_data()

    # Show cart summary for confirmation
    async with async_session() as session:
        cart_repo = CartRepo(session)
        items = await cart_repo.get_items(customer.id)
        total = await cart_repo.get_total(customer.id)

    lines = [
        "📋 <b>Подтверждение заказа:</b>\n",
        f"👤 <b>ФИО:</b> {data['full_name']}",
        f"📱 <b>Телефон:</b> {customer.phone}",
        f"📍 <b>Адрес:</b> {data['address']}\n",
        "<b>Товары:</b>",
    ]
    for item in items:
        lines.append(f"• {item.product.name} × {item.quantity} = {item.product.price * item.quantity}₽")
    lines.append(f"\n💰 <b>Итого: {total}₽</b>")

    # Store temp order data — order_id will be set after creation
    await state.update_data(total=str(total))

    await message.answer(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=order_confirm_keyboard(order_id=0),  # Placeholder
    )


# ─── Step 3: Confirm order ──────────────────────────────────────────


@router.callback_query(OrderCB.filter(F.action == "confirm"), OrderFSM.confirmation)
async def confirm_order(
    callback: CallbackQuery,
    state: FSMContext,
    customer: Customer,
    bot: Bot,
):
    data = await state.get_data()

    try:
        async with async_session() as session:
            cart_repo = CartRepo(session)
            items = await cart_repo.get_items(customer.id)

            if not items:
                await callback.answer("Корзина пуста!", show_alert=True)
                await state.clear()
                return

            order_repo = OrderRepo(session)
            order = await order_repo.create_from_cart(
                customer=customer,
                full_name=data["full_name"],
                address=data["address"],
                cart_items=items,
            )
    except Exception as e:
        logger.error("Failed to create order: %s", e)
        await callback.answer("❌ Ошибка создания заказа. Попробуйте позже.", show_alert=True)
        await state.clear()
        return

    await state.clear()

    # Payment stub message
    await callback.message.edit_text(
        f"✅ <b>Заказ #{order.id} создан!</b>\n\n"
        f"💰 Сумма: {order.total}₽\n\n"
        "💳 Оплатите заказ любым удобным способом.\n"
        "После оплаты нажмите кнопку ниже:",
        parse_mode="HTML",
        reply_markup=order_payment_keyboard(order.id),
    )

    # Notify admin chat
    async with async_session() as session:
        settings_repo = SettingsRepo(session)
        bot_settings = await settings_repo.get()

        if bot_settings and bot_settings.admin_chat_id:
            order_repo = OrderRepo(session)
            order_full = await order_repo.get_by_id(order.id)
            items_text = "\n".join(
                f"• {item.product_name} × {item.quantity} = {item.price * item.quantity}₽"
                for item in order_full.items
            )
            await send_order_to_admin_chat(
                bot=bot,
                admin_chat_id=bot_settings.admin_chat_id,
                order_id=order.id,
                customer_name=order_full.full_name,
                customer_phone=order_full.phone,
                address=order_full.address,
                total=order_full.total,
                items_text=items_text,
                keyboard=admin_order_keyboard(order.id),
            )

    await callback.answer()


# ─── Cancel order ───────────────────────────────────────────────────


@router.callback_query(OrderCB.filter(F.action == "cancel"))
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Заказ отменён.")
    await callback.answer()


# ─── I paid button ──────────────────────────────────────────────────


@router.callback_query(OrderCB.filter(F.action == "paid"))
async def mark_paid(callback: CallbackQuery, callback_data: OrderCB, customer: Customer):
    order_id = callback_data.order_id

    async with async_session() as session:
        repo = OrderRepo(session)
        order = await repo.update_status(order_id, OrderStatus.PAID)

    if order:
        await callback.message.edit_text(
            f"✅ <b>Заказ #{order_id}</b> — оплата отмечена!\n\n"
            "Ожидайте подтверждения от администратора.",
            parse_mode="HTML",
        )
    else:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    await callback.answer("Спасибо за оплату!")


# ─── My orders command ──────────────────────────────────────────────


@router.message(F.text == "📋 Мои заказы")
async def my_orders(message: Message, customer: Customer, state: FSMContext):
    current = await state.get_state()
    if current:
        await state.clear()
        await message.answer("⚠️ Оформление заказа отменено.")
    else:
        await state.clear()

    async with async_session() as session:
        from sqlalchemy import select
        from bot.app.db.models import Order as OrderModel

        result = await session.execute(
            select(OrderModel)
            .where(OrderModel.customer_id == customer.id)
            .order_by(OrderModel.created_at.desc())
            .limit(10)
        )
        orders = list(result.scalars().all())

    if not orders:
        await message.answer("📋 У вас пока нет заказов.")
        return

    lines = ["📋 <b>Ваши заказы:</b>\n"]
    for order in orders:
        status_label = OrderStatus(order.status).label
        lines.append(f"#{order.id} — {status_label} — {order.total}₽ ({order.created_at.strftime('%d.%m.%Y')})")

    await message.answer("\n".join(lines), parse_mode="HTML")
