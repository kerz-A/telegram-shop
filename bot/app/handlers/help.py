from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router(name="help")


HELP_TEXT = (
    "🤖 <b>Помощь</b>\n\n"
    "<b>Команды:</b>\n"
    "/start — Начать работу с ботом\n"
    "/catalog — Открыть каталог товаров\n"
    "/cart — Показать корзину\n"
    "/help — Справка\n\n"
    "<b>Как сделать заказ:</b>\n"
    "1. Выберите товары в каталоге\n"
    "2. Добавьте их в корзину\n"
    "3. Нажмите «Оформить заказ»\n"
    "4. Укажите ФИО и адрес доставки\n"
    "5. Оплатите заказ и нажмите «Я оплатил(а)»\n\n"
    "<b>FAQ:</b>\n"
    "Введите @test_task_tgshopbot в любом чате для поиска по FAQ.\n\n"
    "По всем вопросам обращайтесь к администратору."
)


@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message, state: FSMContext):
    current = await state.get_state()
    if current:
        await state.clear()
        await message.answer("⚠️ Оформление заказа отменено.")
    await message.answer(HELP_TEXT, parse_mode="HTML")
