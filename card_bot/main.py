"""
main.py — Точка входа бота «Создание карточек».

Запускает polling, инициализирует БД.
Вся логика — в пакете handlers/.
"""
import nest_asyncio
nest_asyncio.apply()

import asyncio
import logging
import sys

from telegram import Update

from config import BOT_TOKEN
from database import init_db
from handlers.router import build_application

# ─── Логирование ────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ─── Запуск ─────────────────────────────────────────────────────────────────────
async def main() -> None:
    if not BOT_TOKEN:
        logger.critical("❌ BOT_TOKEN не задан! Добавьте его в файл .env")
        sys.exit(1)

    await init_db()
    logger.info("🤖 Бот «Создание карточек» запускается...")

    app = build_application()
    await app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == '__main__':
    asyncio.run(main())
