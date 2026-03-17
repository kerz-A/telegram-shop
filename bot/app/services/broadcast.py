import asyncio
import logging
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile

from bot.app.db.engine import async_session
from bot.app.db.repositories.repo import BroadcastRepo, CustomerRepo
from shop_core.constants import BROADCAST_RATE_LIMIT
from shop_core.enums import BroadcastStatus

logger = logging.getLogger(__name__)

MEDIA_ROOT = Path("/app/admin_panel/media")


async def run_broadcast(bot: Bot, broadcast_id: int, text: str, image_path: str | None = None):
    """
    Background task: sends broadcast to all customers.
    Rate-limited to BROADCAST_RATE_LIMIT messages per second.
    """
    logger.info("Starting broadcast #%s", broadcast_id)

    async with async_session() as session:
        br_repo = BroadcastRepo(session)
        await br_repo.update_status(broadcast_id, BroadcastStatus.SENDING)

        cust_repo = CustomerRepo(session)
        telegram_ids = await cust_repo.get_all_ids()

    delay = 1.0 / BROADCAST_RATE_LIMIT
    sent = 0
    errors = 0

    for tg_id in telegram_ids:
        try:
            if image_path:
                full_path = Path(image_path)
                if not full_path.is_absolute():
                    full_path = MEDIA_ROOT / image_path
                if full_path.exists():
                    await bot.send_photo(
                        chat_id=tg_id,
                        photo=FSInputFile(full_path),
                        caption=text,
                        parse_mode="HTML",
                    )
                else:
                    await bot.send_message(chat_id=tg_id, text=text, parse_mode="HTML")
            else:
                await bot.send_message(chat_id=tg_id, text=text, parse_mode="HTML")
            sent += 1
        except Exception as e:
            logger.warning("Broadcast #%s: failed to send to %s: %s", broadcast_id, tg_id, e)
            errors += 1

        await asyncio.sleep(delay)

    # Update final stats
    async with async_session() as session:
        br_repo = BroadcastRepo(session)
        broadcast = await br_repo.get_by_id(broadcast_id)
        if broadcast:
            broadcast.sent_count = sent
            broadcast.error_count = errors
            broadcast.status = BroadcastStatus.SENT
            await session.commit()

    logger.info("Broadcast #%s complete: sent=%s, errors=%s", broadcast_id, sent, errors)
