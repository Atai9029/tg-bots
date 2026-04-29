"""
handlers/template_create.py — Создание нового шаблона карточки.

Цепочка состояний:
  CARD_MENU
    → TEMPLATE_SELECT_TYPE   (inline: выбор типа карточки)
    → TEMPLATE_ORG_NAME      (название организации)
    → TEMPLATE_HOLDER_NAME   (владелец)
    → (по типу)
        Визитка:   POSITION → PHONE → EMAIL → WEBSITE → VALIDITY
        Пропуск:   CARD_NUMBER → ACCESS_LEVEL → VALIDITY
        Членство:  MEMBER_TYPE → CARD_NUMBER → VALIDITY
    → TEMPLATE_ADDITIONAL    (доп. информация)
    → TEMPLATE_SAVE_NAME     (название шаблона)
    → TEMPLATE_REVIEW        (превью + кнопка «Завершить»)
    → TEMPLATE_CONFIRM_APPLY (применить сейчас? Да/Нет)
"""

from telegram import Update
from telegram.ext import ContextTypes

from config import (
    MAIN_MENU, CARD_MENU,
    TEMPLATE_SELECT_TYPE, TEMPLATE_ORG_NAME, TEMPLATE_HOLDER_NAME,
    TEMPLATE_POSITION, TEMPLATE_PHONE, TEMPLATE_EMAIL, TEMPLATE_WEBSITE,
    TEMPLATE_CARD_NUMBER, TEMPLATE_ACCESS_LEVEL, TEMPLATE_MEMBER_TYPE,
    TEMPLATE_VALIDITY, TEMPLATE_ADDITIONAL, TEMPLATE_SAVE_NAME,
    TEMPLATE_REVIEW, TEMPLATE_CONFIRM_APPLY,
    BTN_CANCEL, BTN_SKIP, BTN_FINISH,
    CARD_PASS, CARD_MEMBERSHIP, CARD_BUSINESS, CARD_TYPE_LABELS,
)
from database import get_user, save_template, get_template
from keyboards import (
    kb_cancel, kb_skip_cancel, kb_finish_cancel, kb_remove,
    kb_main, ikb_card_types, ikb_yes_no,
)
from handlers.utils import get_draft, clear_draft, template_summary, cancel_to_card_menu, back_to_main
from handlers.card_generation import generate_and_send


# ─── Открытие мастера ───────────────────────────────────────────────────────────

async def handle_create_template(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало: очищаем черновик и предлагаем выбрать тип карточки."""
    clear_draft(ctx)
    await update.message.reply_text(
        "📝 *Создание шаблона*\n\nВыберите тип карточки:",
        parse_mode="Markdown",
        reply_markup=kb_cancel(),
    )
    await update.message.reply_text("👇 Тип карточки:", reply_markup=ikb_card_types())
    return TEMPLATE_SELECT_TYPE


# ─── Шаг 0: Тип карточки ────────────────────────────────────────────────────────

async def cbq_select_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Inline-кнопка выбора типа."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        return await cancel_to_card_menu(query, ctx)

    card_type = query.data.replace("ctype_", "")
    get_draft(ctx)["card_type"] = card_type
    type_name = CARD_TYPE_LABELS.get(card_type, "")

    await query.edit_message_text(f"✅ Выбран тип: *{type_name}*", parse_mode="Markdown")
    await query.message.reply_text(
        "🏢 *Шаг 1 / Название организации*\n\n"
        "Как называется ваша организация, компания или клуб?",
        parse_mode="Markdown",
        reply_markup=kb_cancel(),
    )
    return TEMPLATE_ORG_NAME


# ─── Шаг 1: Организация ─────────────────────────────────────────────────────────

async def handle_org_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == BTN_CANCEL:
        return await cancel_to_card_menu(update.message, ctx)

    get_draft(ctx)["org_name"] = update.message.text.strip()
    await update.message.reply_text(
        "👤 *Шаг 2 / Владелец карточки*\n\nВведите ФИО или имя владельца:",
        parse_mode="Markdown",
        reply_markup=kb_cancel(),
    )
    return TEMPLATE_HOLDER_NAME


# ─── Шаг 2: Владелец → ветвление по типу ───────────────────────────────────────

async def handle_holder_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == BTN_CANCEL:
        return await cancel_to_card_menu(update.message, ctx)

    get_draft(ctx)["holder_name"] = update.message.text.strip()
    card_type = get_draft(ctx).get("card_type")

    if card_type == CARD_BUSINESS:
        await update.message.reply_text(
            "💼 *Шаг 3 / Должность*\n\nУкажите должность или роль:",
            parse_mode="Markdown",
            reply_markup=kb_skip_cancel(),
        )
        return TEMPLATE_POSITION

    if card_type == CARD_PASS:
        await update.message.reply_text(
            "🔢 *Шаг 3 / Номер карты доступа*\n\nВведите номер удостоверения:",
            parse_mode="Markdown",
            reply_markup=kb_skip_cancel(),
        )
        return TEMPLATE_CARD_NUMBER

    if card_type == CARD_MEMBERSHIP:
        await update.message.reply_text(
            "🎫 *Шаг 3 / Тип членства*\n\nНапример: Золото, Премиум, Стандарт:",
            parse_mode="Markdown",
            reply_markup=kb_skip_cancel(),
        )
        return TEMPLATE_MEMBER_TYPE

    return await _ask_validity(update.message, ctx)


# ─── Визитка: должность → телефон → email → сайт ────────────────────────────────

async def handle_position(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == BTN_CANCEL:
        return await cancel_to_card_menu(update.message, ctx)
    if update.message.text != BTN_SKIP:
        get_draft(ctx)["position"] = update.message.text.strip()

    await update.message.reply_text(
        "📞 *Шаг 4 / Телефон*\n\nВведите номер телефона:",
        parse_mode="Markdown",
        reply_markup=kb_skip_cancel(),
    )
    return TEMPLATE_PHONE


async def handle_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == BTN_CANCEL:
        return await cancel_to_card_menu(update.message, ctx)
    if update.message.text != BTN_SKIP:
        get_draft(ctx)["phone"] = update.message.text.strip()

    await update.message.reply_text(
        "📧 *Шаг 5 / Email*\n\nВведите адрес электронной почты:",
        parse_mode="Markdown",
        reply_markup=kb_skip_cancel(),
    )
    return TEMPLATE_EMAIL


async def handle_email(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == BTN_CANCEL:
        return await cancel_to_card_menu(update.message, ctx)
    if update.message.text != BTN_SKIP:
        get_draft(ctx)["email"] = update.message.text.strip()

    await update.message.reply_text(
        "🌐 *Шаг 6 / Веб-сайт*\n\nВведите адрес сайта:",
        parse_mode="Markdown",
        reply_markup=kb_skip_cancel(),
    )
    return TEMPLATE_WEBSITE


async def handle_website(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == BTN_CANCEL:
        return await cancel_to_card_menu(update.message, ctx)
    if update.message.text != BTN_SKIP:
        get_draft(ctx)["website"] = update.message.text.strip()
    return await _ask_validity(update.message, ctx)


# ─── Пропуск: номер карты → уровень доступа ─────────────────────────────────────

async def handle_card_number(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == BTN_CANCEL:
        return await cancel_to_card_menu(update.message, ctx)
    if update.message.text != BTN_SKIP:
        get_draft(ctx)["card_number"] = update.message.text.strip()

    await update.message.reply_text(
        "🔑 *Уровень доступа*\n\nНапример: A1, Все зоны, Только офис:",
        parse_mode="Markdown",
        reply_markup=kb_skip_cancel(),
    )
    return TEMPLATE_ACCESS_LEVEL


async def handle_access_level(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == BTN_CANCEL:
        return await cancel_to_card_menu(update.message, ctx)
    if update.message.text != BTN_SKIP:
        get_draft(ctx)["access_level"] = update.message.text.strip()
    return await _ask_validity(update.message, ctx)


# ─── Членство: тип → номер карты ────────────────────────────────────────────────

async def handle_member_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == BTN_CANCEL:
        return await cancel_to_card_menu(update.message, ctx)
    if update.message.text != BTN_SKIP:
        get_draft(ctx)["membership_type"] = update.message.text.strip()

    await update.message.reply_text(
        "🔢 *Номер карты членства*\n\nВведите ID или номер:",
        parse_mode="Markdown",
        reply_markup=kb_skip_cancel(),
    )
    return TEMPLATE_CARD_NUMBER


# ─── Общие поля: срок действия → доп. информация ────────────────────────────────

async def _ask_validity(msg, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    await msg.reply_text(
        "📅 *Срок действия*\n\nВведите дату окончания (например: 31.12.2026):",
        parse_mode="Markdown",
        reply_markup=kb_skip_cancel(),
    )
    return TEMPLATE_VALIDITY


async def handle_validity(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == BTN_CANCEL:
        return await cancel_to_card_menu(update.message, ctx)
    if update.message.text != BTN_SKIP:
        get_draft(ctx)["validity_date"] = update.message.text.strip()

    await update.message.reply_text(
        "📝 *Дополнительная информация*\n\n"
        "Любой текст, который хотите добавить на карточку:",
        parse_mode="Markdown",
        reply_markup=kb_skip_cancel(),
    )
    return TEMPLATE_ADDITIONAL


async def handle_additional(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == BTN_CANCEL:
        return await cancel_to_card_menu(update.message, ctx)
    if update.message.text != BTN_SKIP:
        get_draft(ctx)["additional_info"] = update.message.text.strip()

    await update.message.reply_text(
        "🏷 *Название шаблона*\n\n"
        "Придумайте название (например: «Карта сотрудника 2025»):",
        parse_mode="Markdown",
        reply_markup=kb_cancel(),
    )
    return TEMPLATE_SAVE_NAME


# ─── Название → превью → подтверждение ──────────────────────────────────────────

async def handle_save_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == BTN_CANCEL:
        return await cancel_to_card_menu(update.message, ctx)

    get_draft(ctx)["template_name"] = update.message.text.strip()
    summary = template_summary(get_draft(ctx))

    await update.message.reply_text(
        summary + "\n\nВсё верно? Нажмите *«✅ Завершить шаблон»* для сохранения.",
        parse_mode="Markdown",
        reply_markup=kb_finish_cancel(),
    )
    return TEMPLATE_REVIEW


async def handle_template_review(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Превью шаблона. Ждём кнопку «Завершить» или «Отмена»."""
    if update.message.text == BTN_CANCEL:
        return await cancel_to_card_menu(update.message, ctx)

    if update.message.text != BTN_FINISH:
        await update.message.reply_text(
            "Нажмите *«✅ Завершить шаблон»* или *«❌ Отмена»*.",
            parse_mode="Markdown",
            reply_markup=kb_finish_cancel(),
        )
        return TEMPLATE_REVIEW

    # Сохраняем в БД
    db_user = await get_user(update.effective_user.id)
    template_id = await save_template(db_user["id"], get_draft(ctx))
    ctx.user_data["last_template_id"] = template_id

    await update.message.reply_text(
        "✅ *Шаблон сохранён!*\n\nПрименить его прямо сейчас и сгенерировать карточку?",
        parse_mode="Markdown",
        reply_markup=kb_remove(),
    )
    await update.message.reply_text(
        "Применить шаблон?",
        reply_markup=ikb_yes_no("apply_yes", "apply_no"),
    )
    return TEMPLATE_CONFIRM_APPLY


# ─── Inline: применить шаблон сразу? ────────────────────────────────────────────

async def cbq_apply_yes(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Да — запускаем генерацию карточки."""
    query = update.callback_query
    await query.answer()

    template_id = ctx.user_data.get("last_template_id")
    template = await get_template(template_id) if template_id else None

    if not template:
        await query.edit_message_text("⚠️ Шаблон не найден.")
        return await back_to_main(query.message, ctx)

    await query.edit_message_text("⏳ Ожидайте, ИИ создаёт карточку...")
    return await generate_and_send(query.message, ctx, template, update.effective_user.id)


async def cbq_apply_no(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Нет — просто сохраняем, возвращаем в главное меню."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📋 Шаблон сохранён. Используйте его через «📋 Использовать шаблон»."
    )
    clear_draft(ctx)
    await query.message.reply_text("🏠 Главное меню:", reply_markup=kb_main())
    return MAIN_MENU
