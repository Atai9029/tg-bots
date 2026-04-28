from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


class MainMenuCb(CallbackData, prefix="main"):
    action: str


class TemplateCb(CallbackData, prefix="tpl"):
    action: str
    template_id: int | None = None


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data="cancel")]]
    )


def yes_no_kb(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Да", callback_data=yes_data), InlineKeyboardButton(text="Нет", callback_data=no_data)], [InlineKeyboardButton(text="Отмена", callback_data="cancel")]]
    )


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Профиль")],
            [KeyboardButton(text="Генерация карточек")],
            [KeyboardButton(text="Помощь")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def generation_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Создать шаблон", callback_data="gen:create")],
            [InlineKeyboardButton(text="Использовать шаблон", callback_data="gen:use")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
        ]
    )


def template_selection_kb(items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=name, callback_data=TemplateCb(action="pick", template_id=template_id).pack())] for template_id, name in items]
    rows.append([InlineKeyboardButton(text="Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def finish_template_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Завершить шаблон", callback_data="tpl:finish")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
        ]
    )
