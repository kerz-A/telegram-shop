import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from bot.app.db.engine import async_session
from bot.app.db.repositories.repo import CustomerRepo

logger = logging.getLogger(__name__)


class RegistrationMiddleware(BaseMiddleware):
    """
    On every update: get or create customer in DB,
    inject customer object into handler data.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Extract user from update
        user = data.get("event_from_user")
        if user is None or user.is_bot:
            return await handler(event, data)

        async with async_session() as session:
            repo = CustomerRepo(session)
            customer, created = await repo.get_or_create(
                telegram_id=user.id,
                first_name=user.first_name or "",
                last_name=user.last_name or "",
                username=user.username or "",
            )
            data["customer"] = customer
            data["session"] = session

            if created:
                logger.info("New customer registered: %s (tg_id=%s)", user.first_name, user.id)

            return await handler(event, data)
