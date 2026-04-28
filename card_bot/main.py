from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from config import settings
from db import db
from handlers.common import router as common_router
from handlers.templates import router as templates_router

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not set")

    await db.connect()
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(common_router)
    dp.include_router(templates_router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
