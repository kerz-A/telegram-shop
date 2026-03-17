import logging
import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.app.db.engine import async_session
from bot.app.db.repositories.repo import SettingsRepo
from shop_core.constants import SETTINGS_CACHE_TTL

logger = logging.getLogger(__name__)


class SubscriptionMiddleware(BaseMiddleware):
    """
    Check that the user is subscribed to all required channels.
    Channel list is loaded from DB (BotSettings) with in-memory caching.
    """

    def __init__(self):
        self._cache: list[str] = []
        self._cache_ts: float = 0

    async def _get_channels(self) -> list[str]:
        now = time.time()
        if self._cache and (now - self._cache_ts) < SETTINGS_CACHE_TTL:
            return self._cache

        async with async_session() as session:
            repo = SettingsRepo(session)
            settings = await repo.get()
            if settings and settings.required_channels:
                self._cache = settings.required_channels
            else:
                self._cache = []
            self._cache_ts = now
        return self._cache

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        channels = await self._get_channels()
        if not channels:
            return await handler(event, data)

        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        bot: Bot = data["bot"]
        not_subscribed: list[str] = []

        for channel in channels:
            try:
                member = await bot.get_chat_member(chat_id=channel, user_id=user.id)
                if member.status in ("left", "kicked"):
                    not_subscribed.append(channel)
            except Exception as e:
                logger.warning("Cannot check subscription for %s: %s", channel, e)

        if not_subscribed:
            text = (
                "❌ Для использования бота необходимо подписаться на каналы:\n\n"
                + "\n".join(f"👉 {ch}" for ch in not_subscribed)
                + "\n\nПосле подписки попробуйте снова."
            )
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.answer("Подпишитесь на каналы!", show_alert=True)
                await event.message.answer(text)
            return  # Block handler

        return await handler(event, data)
