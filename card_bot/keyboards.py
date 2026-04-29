"""
keyboards.py – All ReplyKeyboard and InlineKeyboard layouts.
"""

from telegram import (
    ReplyKeyboardMarkup, ReplyKeyboardRemove,
    InlineKeyboardButton, InlineKeyboardMarkup,
)
from config import (
    BTN_PROFILE, BTN_GENERATE, BTN_HELP,
    BTN_CREATE_TPL, BTN_USE_TPL, BTN_BACK,
    BTN_CANCEL, BTN_SKIP, BTN_FINISH,
    CARD_PASS, CARD_MEMBERSHIP, CARD_BUSINESS, CARD_TYPE_LABELS,
)


# ─── Reply Keyboards ────────────────────────────────────────────────────────────

def kb_main() -> ReplyKeyboardMarkup:
    """Main menu keyboard."""
    return ReplyKeyboardMarkup(
        [[BTN_PROFILE], [BTN_GENERATE], [BTN_HELP]],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие...",
    )


def kb_cards() -> ReplyKeyboardMarkup:
    """Card generation submenu."""
    return ReplyKeyboardMarkup(
        [[BTN_CREATE_TPL], [BTN_USE_TPL], [BTN_BACK]],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие...",
    )


def kb_cancel() -> ReplyKeyboardMarkup:
    """Single cancel button."""
    return ReplyKeyboardMarkup(
        [[BTN_CANCEL]],
        resize_keyboard=True,
    )


def kb_skip_cancel() -> ReplyKeyboardMarkup:
    """Skip + Cancel."""
    return ReplyKeyboardMarkup(
        [[BTN_SKIP], [BTN_CANCEL]],
        resize_keyboard=True,
    )


def kb_finish_cancel() -> ReplyKeyboardMarkup:
    """Finish template + Cancel."""
    return ReplyKeyboardMarkup(
        [[BTN_FINISH], [BTN_CANCEL]],
        resize_keyboard=True,
    )


def kb_remove() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


# ─── Inline Keyboards ───────────────────────────────────────────────────────────

def ikb_card_types() -> InlineKeyboardMarkup:
    """Inline buttons for card type selection."""
    buttons = [
        [InlineKeyboardButton(CARD_TYPE_LABELS[CARD_PASS],       callback_data=f"ctype_{CARD_PASS}")],
        [InlineKeyboardButton(CARD_TYPE_LABELS[CARD_MEMBERSHIP], callback_data=f"ctype_{CARD_MEMBERSHIP}")],
        [InlineKeyboardButton(CARD_TYPE_LABELS[CARD_BUSINESS],   callback_data=f"ctype_{CARD_BUSINESS}")],
        [InlineKeyboardButton("❌ Отмена",                        callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(buttons)


def ikb_yes_no(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Да", callback_data=yes_data),
        InlineKeyboardButton("❌ Нет", callback_data=no_data),
    ]])


def ikb_templates(templates: list[dict]) -> InlineKeyboardMarkup:
    """List of user templates as inline buttons."""
    rows = []
    for t in templates:
        label = f"{CARD_TYPE_LABELS.get(t['card_type'], '📄')}  {t['template_name']}"
        rows.append([InlineKeyboardButton(label, callback_data=f"tpl_{t['id']}")])
    rows.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(rows)


def ikb_cancel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]])
