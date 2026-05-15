from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent

from config.settings import settings
from handlers import download, search, start
from utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


async def global_error_handler(event: ErrorEvent) -> None:
    logger.critical(
        'Unhandled exception update_id=%s exc=%r',
        getattr(event.update, 'update_id', '?'),
        event.exception,
        exc_info=event.exception,
    )


def create_bot() -> Bot:
    return Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(download.router)
    dp.include_router(search.router)
    dp.error.register(global_error_handler)
    return dp


async def main() -> None:
    bot = create_bot()
    dp = create_dispatcher()

    try:
        me = await bot.get_me()
        logger.info('Bot started username=@%s id=%d', me.username, me.id)
    except Exception as exc:
        logger.critical('Cannot connect to Telegram API: %s', exc)
        sys.exit(1)

    logger.info('Starting long-polling… (press Ctrl+C to stop)')
    await dp.start_polling(bot, allowed_updates=['message', 'callback_query'])


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Interrupted by user — shutting down.')
