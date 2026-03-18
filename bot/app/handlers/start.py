import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.app.config import settings
from bot.app.db.engine import async_session
from bot.app.db.models import Customer
from bot.app.db.repositories.repo import CustomerRepo, ProductRepo
from bot.app.keyboards.inline import product_card_keyboard
from bot.app.keyboards.reply import contact_keyboard, main_menu_keyboard
from bot.app.services.media import build_product_media_group

logger = logging.getLogger(__name__)

router = Router(name="start")


@router.message(CommandStart(deep_link=True))
async def cmd_start_deep_link(message: Message, customer: Customer, command: CommandStart, state: FSMContext):
    """Handle /start with deep link parameter, e.g. product_123."""
    await state.clear()
    payload = command.args

    if payload and payload.startswith("product_"):
        try:
            product_id = int(payload.split("_", 1)[1])
        except (ValueError, IndexError):
            await message.answer("❌ Неверная ссылка на товар.")
            return

        async with async_session() as session:
            repo = ProductRepo(session)
            product = await repo.get_by_id(product_id)

        if not product:
            await message.answer("❌ Товар не найден или неактивен.")
            return

        # Send product card
        media_group = build_product_media_group(product)
        if media_group:
            await message.answer_media_group(media=media_group)

        text = (
            f"<b>{product.name}</b>\n\n"
            f"{product.description}\n\n"
            f"💰 <b>{product.price}₽</b>\n"
            f"📁 {product.category.name}"
        )
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=product_card_keyboard(product, product.category_id),
        )
        return

    # Unknown deep link — fallback to normal start
    await _handle_start(message, customer)


@router.message(CommandStart())
async def cmd_start(message: Message, customer: Customer, state: FSMContext):
    """Handle /start without deep link."""
    await state.clear()
    await _handle_start(message, customer)


async def _handle_start(message: Message, customer: Customer):
    """Registration flow: request contact if phone is missing."""
    if not customer.phone:
        await message.answer(
            "👋 Добро пожаловать в магазин!\n\n"
            "Для начала работы нажмите кнопку\n"
            "📱 <b>«Поделиться контактом»</b> ниже.\n\n"
            "<i>Ввод номера вручную не поддерживается — "
            "используйте кнопку.</i>",
            parse_mode="HTML",
            reply_markup=contact_keyboard(),
        )
    else:
        await message.answer(
            f"👋 С возвращением, {customer.first_name}!\n\n"
            "Выберите действие:",
            reply_markup=main_menu_keyboard(settings.webapp_url),
        )


@router.message(F.contact)
async def handle_contact(message: Message, customer: Customer):
    """Save phone from shared contact."""
    contact = message.contact

    # Only accept user's own contact
    if contact.user_id != message.from_user.id:
        await message.answer("❌ Пожалуйста, отправьте свой контакт.")
        return

    phone = contact.phone_number
    if not phone.startswith("+"):
        phone = f"+{phone}"

    async with async_session() as session:
        repo = CustomerRepo(session)
        await repo.set_phone(message.from_user.id, phone)

    await message.answer(
        f"✅ Номер {phone} сохранён!\n\n"
        "Теперь вы можете пользоваться магазином. Выберите действие:",
        reply_markup=main_menu_keyboard(settings.webapp_url),
    )


async def _no_phone(message: Message, customer: Customer, **kwargs) -> bool:
    """Filter: only match if customer has no phone."""
    return not customer.phone


@router.message(F.text, _no_phone)
async def handle_text_without_phone(message: Message, customer: Customer):
    """Catch text input from users who haven't shared their phone yet."""
    await message.answer(
        "⚠️ Пожалуйста, нажмите кнопку <b>«📱 Поделиться контактом»</b> ниже.\n\n"
        "Ввод номера вручную не поддерживается.",
        parse_mode="HTML",
        reply_markup=contact_keyboard(),
    )
