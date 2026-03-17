import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

logger = logging.getLogger("bot.updates")


class LoggingMiddleware(BaseMiddleware):
    """Log every incoming update: telegram_id, update type, timestamp."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        telegram_id = user.id if user else "unknown"

        update = data.get("event_update")
        if update:
            update_type = update.event_type
        else:
            update_type = type(event).__name__

        timestamp = datetime.now(timezone.utc).isoformat()

        logger.info(
            "update | tg_id=%s | type=%s | ts=%s",
            telegram_id,
            update_type,
            timestamp,
        )

        return await handler(event, data)
