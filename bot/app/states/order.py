from aiogram.fsm.state import State, StatesGroup


class OrderFSM(StatesGroup):
    full_name = State()
    address = State()
    confirmation = State()
