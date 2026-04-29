"""
handlers/template_use.py — Выбор и применение сохранённого шаблона.

Цепочка состояний:
  CARD_MENU
    → SELECT_SAVED_TEMPLATE   (inline-список сохранённых шаблонов)
    → CONFIRM_USE_TEMPLATE    (Использовать этот шаблон? Да/Нет)
    → генерация карточки      (если Да) / MAIN_MENU (если Нет)
"""

from telegram import Update
from telegram.ext import ContextTypes

from config import (
    MAIN_MENU, CARD_MENU,
    SELECT_SAVED_TEMPLATE, CONFIRM_USE_TEMPLATE,
)
from database import get_user, get_templates, get_template
from keyboards import kb_cancel, kb_cards, kb_main, ikb_templates, ikb_yes_no
from handlers.utils import clear_draft, template_summary, cancel_to_card_menu, back_to_main
from handlers.card_generation import generate_and_send


async def handle_use_template(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает список сохранённых шаблонов пользователя."""
    db_user   = await get_user(update.effective_user.id)
    templates = await get_templates(db_user["id"])

    if not templates:
        await update.message.reply_text(
            "📭 У вас пока нет сохранённых шаблонов.\n"
            "Сначала создайте шаблон через «📝 Создать шаблон».",
            reply_markup=kb_cards(),
        )
        return CARD_MENU

    await update.message.reply_text(
        f"📋 *Ваши шаблоны* ({len(templates)} шт.):\n\nВыберите шаблон:",
        parse_mode="Markdown",
        reply_markup=kb_cancel(),
    )
    await update.message.reply_text("👇 Шаблоны:", reply_markup=ikb_templates(templates))
    return SELECT_SAVED_TEMPLATE


async def cbq_template_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Пользователь выбрал шаблон — показываем превью и спрашиваем подтверждение."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        return await cancel_to_card_menu(query, ctx)

    template_id = int(query.data.replace("tpl_", ""))
    template    = await get_template(template_id)

    if not template:
        await query.edit_message_text("⚠️ Шаблон не найден.")
        return CARD_MENU

    ctx.user_data["selected_template_id"] = template_id
    summary = template_summary(template)

    await query.edit_message_text(
        summary + "\n\nИспользовать этот шаблон?",
        parse_mode="Markdown",
        reply_markup=ikb_yes_no("use_yes", "use_no"),
    )
    return CONFIRM_USE_TEMPLATE


async def cbq_use_yes(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Да — запускаем генерацию карточки по выбранному шаблону."""
    query = update.callback_query
    await query.answer()

    template_id = ctx.user_data.get("selected_template_id")
    template    = await get_template(template_id) if template_id else None

    if not template:
        await query.edit_message_text("⚠️ Шаблон не найден.")
        return await back_to_main(query.message, ctx)

    await query.edit_message_text("⏳ Ожидайте, ИИ создаёт карточку...")
    return await generate_and_send(query.message, ctx, template, update.effective_user.id)


async def cbq_use_no(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Нет — отменяем, возвращаем в главное меню."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Отменено.")
    clear_draft(ctx)
    await query.message.reply_text("🏠 Главное меню:", reply_markup=kb_main())
    return MAIN_MENU
