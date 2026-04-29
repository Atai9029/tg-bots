"""
handlers/utils.py — Вспомогательные функции, общие для всех хэндлеров.

  get_draft()          — черновик шаблона в user_data
  clear_draft()        — очистка временных данных
  template_summary()   — текстовое превью шаблона
  cancel_to_card_menu()— отмена → подменю карточек
  back_to_main()       — возврат в главное меню
"""

from telegram.ext import ContextTypes

from config import CARD_TYPE_LABELS, CARD_MENU, MAIN_MENU
from keyboards import kb_main, kb_cards


# ─── Черновик шаблона ───────────────────────────────────────────────────────────

def get_draft(ctx: ContextTypes.DEFAULT_TYPE) -> dict:
    """Возвращает (или создаёт) черновик шаблона в user_data."""
    if "template_draft" not in ctx.user_data:
        ctx.user_data["template_draft"] = {}
    return ctx.user_data["template_draft"]


def clear_draft(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Удаляет черновик и все временные ключи из user_data."""
    ctx.user_data.pop("template_draft", None)
    ctx.user_data.pop("selected_template_id", None)
    ctx.user_data.pop("last_template_id", None)


# ─── Форматирование превью ───────────────────────────────────────────────────────

def template_summary(data: dict) -> str:
    """Возвращает читаемое превью шаблона в формате Markdown."""
    ctype = CARD_TYPE_LABELS.get(data.get("card_type", ""), "—")
    lines = [
        "📋 *Предварительный просмотр шаблона:*\n",
        f"🏷 Тип карты:    {ctype}",
        f"🏢 Организация:  {data.get('org_name', '—')}",
        f"👤 Владелец:     {data.get('holder_name', '—')}",
    ]
    optional = [
        ("💼 Должность",       "position"),
        ("📞 Телефон",         "phone"),
        ("📧 Email",           "email"),
        ("🌐 Сайт",            "website"),
        ("🔢 Номер карты",     "card_number"),
        ("🔑 Уровень доступа", "access_level"),
        ("🎫 Тип членства",    "membership_type"),
        ("📅 Срок действия",   "validity_date"),
        ("📝 Доп. информация", "additional_info"),
    ]
    for label, key in optional:
        if data.get(key):
            lines.append(f"{label}: {data[key]}")
    return "\n".join(lines)


# ─── Навигация ───────────────────────────────────────────────────────────────────

async def cancel_to_card_menu(target, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена действия → возврат в подменю генерации карточек."""
    clear_draft(ctx)
    text = "❌ Отменено. Возврат в меню карточек."
    if hasattr(target, "edit_message_text"):
        await target.edit_message_text(text)
        await target.message.reply_text("Меню:", reply_markup=kb_cards())
    else:
        await target.reply_text(text, reply_markup=kb_cards())
    return CARD_MENU


async def back_to_main(message, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Возврат в главное меню с очисткой черновика."""
    clear_draft(ctx)
    await message.reply_text("🏠 Главное меню:", reply_markup=kb_main())
    return MAIN_MENU
