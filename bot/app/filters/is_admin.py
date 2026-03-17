from aiogram.filters import BaseFilter
from aiogram.types import Message

from bot.app.db.models import Customer


class IsAdmin(BaseFilter):
    """Check if the user is an admin. Requires RegistrationMiddleware."""

    async def __call__(self, message: Message, customer: Customer | None = None) -> bool:
        if customer is None:
            return False
        return customer.is_admin
