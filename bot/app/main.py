"""
Telegram Shop Bot — Entry Point.
Starts the bot polling and the internal aiohttp webhook server concurrently.
"""

import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiohttp import web

from bot.app.config import settings
from bot.app.handlers import admin_chat, cart, catalog, faq, help, order, start
from bot.app.middlewares.logging import LoggingMiddleware
from bot.app.middlewares.registration import RegistrationMiddleware
from bot.app.middlewares.subscription import SubscriptionMiddleware
from bot.app.webhook_server import create_webhook_app


def setup_logging():
    """Configure logging with file rotation."""
    log_dir = Path("/app/bot/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_dir / "bot.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Silence noisy loggers
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


async def set_bot_commands(bot: Bot):
    """Register bot commands menu."""
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="catalog", description="Каталог товаров"),
        BotCommand(command="cart", description="Корзина"),
        BotCommand(command="help", description="Помощь"),
    ]
    await bot.set_my_commands(commands)


async def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Telegram Shop Bot...")

    # Initialize bot
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Initialize dispatcher
    dp = Dispatcher()

    # Register middleware (order matters!)
    # 1. Logging — first, logs everything
    dp.update.outer_middleware(LoggingMiddleware())
    # 2. Registration — creates/gets customer, injects into data
    dp.update.outer_middleware(RegistrationMiddleware())
    # 3. Subscription check — blocks unsubscribed users
    dp.message.outer_middleware(SubscriptionMiddleware())
    dp.callback_query.outer_middleware(SubscriptionMiddleware())

    # Register routers
    dp.include_routers(
        start.router,
        catalog.router,
        cart.router,
        order.router,
        admin_chat.router,
        faq.router,
        help.router,
    )

    # Set bot commands
    await set_bot_commands(bot)
    logger.info("Bot commands registered")

    # Create webhook server
    webhook_app = create_webhook_app(bot)
    runner = web.AppRunner(webhook_app)
    await runner.setup()
    site = web.TCPSite(
        runner,
        settings.bot_webhook_host,
        settings.bot_webhook_port,
    )
    await site.start()
    logger.info(
        "Webhook server started on %s:%s",
        settings.bot_webhook_host,
        settings.bot_webhook_port,
    )

    # Start polling
    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await runner.cleanup()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
