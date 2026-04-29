"""
handlers/registration.py — Регистрация нового пользователя.

Состояния: REGISTER_NAME → REGISTER_AGE → MAIN_MENU
"""

from telegram import Update
from telegram.ext import ContextTypes

from config import REGISTER_NAME, REGISTER_AGE, MAIN_MENU
from database import get_user, create_user
from keyboards import kb_main, kb_remove


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Точка входа: приветствие или показ меню для уже зарегистрированных."""
    user = update.effective_user
    existing = await get_user(user.id)

    if existing:
        await update.message.reply_text(
            f"👋 С возвращением, *{existing['name']}*\\!",
            parse_mode="MarkdownV2",
            reply_markup=kb_main(),
        )
        return MAIN_MENU

    await update.message.reply_text(
        "🎉 *Добро пожаловать в бота «Создание карточек»\\!*\n\n"
        "Здесь вы можете создавать:\n"
        "  🔐 Пропускные карты\n"
        "  🎫 Карты членства\n"
        "  💼 Визитки\n\n"
        "Для начала давайте познакомимся\\.\n"
        "📝 *Как вас зовут?*",
        parse_mode="MarkdownV2",
        reply_markup=kb_remove(),
    )
    return REGISTER_NAME


async def handle_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем имя пользователя и спрашиваем возраст."""
    name = update.message.text.strip()

    if len(name) < 2 or len(name) > 60:
        await update.message.reply_text(
            "⚠️ Пожалуйста, введите корректное имя (от 2 до 60 символов)."
        )
        return REGISTER_NAME

    ctx.user_data["reg_name"] = name
    await update.message.reply_text(
        f"Приятно познакомиться, *{name}*\\! 😊\n\n📅 *Сколько вам лет?*",
        parse_mode="MarkdownV2",
    )
    return REGISTER_AGE


async def handle_age(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем возраст, сохраняем пользователя в БД и открываем главное меню."""
    text = update.message.text.strip()

    if not text.isdigit() or not (1 <= int(text) <= 120):
        await update.message.reply_text(
            "⚠️ Введите корректный возраст (число от 1 до 120)."
        )
        return REGISTER_AGE

    age  = int(text)
    name = ctx.user_data.pop("reg_name")
    user = update.effective_user

    await create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        name=name,
        age=age,
    )

    await update.message.reply_text(
        f"✅ *Регистрация завершена\\!*\n\n"
        f"👤 Имя: {name}\n"
        f"🎂 Возраст: {age} лет\n\n"
        f"Теперь вы можете создавать карточки\\. Выберите действие ниже 👇",
        parse_mode="MarkdownV2",
        reply_markup=kb_main(),
    )
    return MAIN_MENU
