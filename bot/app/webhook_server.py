"""
Lightweight aiohttp server running alongside the bot.
Receives webhooks from Django (order status changes, broadcast triggers).
"""

import asyncio
import logging

from aiohttp import web
from aiogram import Bot

from bot.app.services.broadcast import run_broadcast
from bot.app.services.notification import notify_order_status
from shop_core.constants import ACTION_ORDER_STATUS_CHANGED, ACTION_START_BROADCAST
from shop_core.enums import OrderStatus
from shop_core.schemas import WebhookPayload

logger = logging.getLogger(__name__)


async def handle_webhook(request: web.Request) -> web.Response:
    """Process incoming webhook from Django."""
    try:
        body = await request.json()
        payload = WebhookPayload(**body)
    except Exception as e:
        logger.error("Invalid webhook payload: %s", e)
        return web.json_response({"error": "Invalid payload"}, status=400)

    bot: Bot = request.app["bot"]

    if payload.action == ACTION_ORDER_STATUS_CHANGED:
        data = payload.data
        await notify_order_status(
            bot=bot,
            telegram_id=data["customer_telegram_id"],
            order_id=data["order_id"],
            new_status=OrderStatus(data["new_status"]),
            message=data.get("message"),
        )
        return web.json_response({"status": "ok"})

    elif payload.action == ACTION_START_BROADCAST:
        data = payload.data
        # Run broadcast as a background task
        asyncio.create_task(
            run_broadcast(
                bot=bot,
                broadcast_id=data["broadcast_id"],
                text=data["text"],
                image_path=data.get("image_path"),
            )
        )
        return web.json_response({"status": "broadcast_started"})

    else:
        logger.warning("Unknown webhook action: %s", payload.action)
        return web.json_response({"error": "Unknown action"}, status=400)


def create_webhook_app(bot: Bot) -> web.Application:
    """Create aiohttp app for internal webhooks."""
    app = web.Application()
    app["bot"] = bot
    app.router.add_post("/webhook", handle_webhook)
    return app
