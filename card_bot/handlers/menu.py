"""
handlers/menu.py — Главное меню и глобальные команды.

  handle_profile()       — показ профиля и статистики
  handle_help()          — инструкция по боту
  handle_generate_menu() — переход в подменю карточек
  handle_back_to_main()  — возврат из подменю в главное меню
  cmd_cancel()           — глобальная отмена /cancel или кнопка «Отмена»
  error_handler()        — логирование ошибок Telegram
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import MAIN_MENU, CARD_MENU
from database import get_user, get_stats
from keyboards import kb_main, kb_cards
from handlers.utils import clear_draft

logger = logging.getLogger(__name__)


async def handle_profile(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает профиль пользователя и его статистику."""
    u = await get_user(update.effective_user.id)
    if not u:
        await update.message.reply_text("⚠️ Профиль не найден. Введите /start")
        return MAIN_MENU

    stats  = await get_stats(u["id"])
    joined = u.get("created_at", "—")
    if isinstance(joined, str) and "T" in joined:
        joined = joined.split("T")[0]

    await update.message.reply_text(
        "👤 *Ваш профиль*\n\n"
        f"🏷 Имя:              {u['name']}\n"
        f"🎂 Возраст:          {u['age']} лет\n"
        f"📅 Регистрация:      {joined}\n\n"
        f"📋 Шаблонов:         {stats['templates']}\n"
        f"🎴 Карточек создано: {stats['generated']}",
        parse_mode="Markdown",
        reply_markup=kb_main(),
    )
    return MAIN_MENU


async def handle_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Отправляет инструкцию по использованию бота."""
    await update.message.reply_text(
        "❓ *Помощь*\n\n"
        "Бот создаёт профессиональные карточки трёх видов:\n\n"
        "🔐 *Пропускная карта* — для контроля доступа\n"
        "🎫 *Карта членства* — для клубов и организаций\n"
        "💼 *Визитка* — деловая карточка\n\n"
        "📌 *Как создать карточку:*\n"
        "1\\. Нажмите «🎴 Генерация карточек»\n"
        "2\\. Выберите «📝 Создать шаблон»\n"
        "3\\. Заполните поля \\(необязательные можно пропустить\\)\n"
        "4\\. Нажмите «✅ Завершить шаблон»\n"
        "5\\. Подтвердите — ИИ сгенерирует карточку\\!\n\n"
        "📌 *Как использовать сохранённый шаблон:*\n"
        "1\\. Нажмите «🎴 Генерация карточек»\n"
        "2\\. Выберите «📋 Использовать шаблон»\n"
        "3\\. Выберите нужный и подтвердите\n\n"
        "❌ В любой момент нажмите «Отмена» для выхода\\.",
        parse_mode="MarkdownV2",
        reply_markup=kb_main(),
    )
    return MAIN_MENU


async def handle_generate_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Открывает подменю генерации карточек."""
    await update.message.reply_text(
        "🎴 *Генерация карточек*\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=kb_cards(),
    )
    return CARD_MENU


async def handle_back_to_main(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Кнопка «Назад» из подменю карточек в главное меню."""
    clear_draft(ctx)
    await update.message.reply_text("🏠 Главное меню:", reply_markup=kb_main())
    return MAIN_MENU


async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Глобальная отмена: /cancel или кнопка «❌ Отмена»."""
    clear_draft(ctx)
    await update.message.reply_text("❌ Действие отменено.", reply_markup=kb_main())
    return MAIN_MENU


async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Логирует необработанные ошибки Telegram."""
    logger.error("Update %s вызвал ошибку: %s", update, ctx.error, exc_info=True)
