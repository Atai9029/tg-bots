"""
handlers/card_generation.py — Генерация карточки через ИИ и отправка пользователю.

  generate_and_send() — вызывает Gemini, рендерит изображение, сохраняет в БД, отправляет фото.
"""

import logging

from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from config import MAIN_MENU
from database import get_user, save_card
from keyboards import kb_main
from ai_generator import generate_card_content
from card_renderer import render_card_bytes
from handlers.utils import clear_draft

logger = logging.getLogger(__name__)


async def generate_and_send(
    message,
    ctx: ContextTypes.DEFAULT_TYPE,
    template: dict,
    telegram_user_id: int,
) -> int:
    """
    Основная функция генерации:
      1. Вызывает Google Gemini для создания контента карточки
      2. Рендерит PNG-изображение через Pillow
      3. Сохраняет запись в БД
      4. Отправляет карточку пользователю как фото
    """
    try:
        await message.reply_chat_action(ChatAction.UPLOAD_PHOTO)

        # 1. Получить контент от ИИ
        ai_data = await generate_card_content(template)

        # 2. Отрисовать изображение
        img_buf = render_card_bytes(template, ai_data)

        # 3. Записать в БД
        db_user = await get_user(telegram_user_id)
        await save_card(
            user_id=db_user["id"],
            template_id=template["id"],
            ai_content=str(ai_data),
            image_path="buffer",
        )

        # 4. Сформировать подпись
        caption = (
            f"🎴 *{ai_data.get('headline', 'Карточка')}*\n"
            f"🏢 {template.get('org_name', '')}\n"
            f"👤 {template.get('holder_name', '')}\n"
            f"🔢 {ai_data.get('card_number_display', '')}"
        )

        # 5. Отправить фото
        await message.reply_photo(
            photo=img_buf,
            caption=caption,
            parse_mode="Markdown",
        )
        await message.reply_text(
            "✅ Карточка успешно создана\\! Сохраните её в галерею\\.",
            parse_mode="MarkdownV2",
            reply_markup=kb_main(),
        )

    except Exception as e:
        logger.error("Ошибка генерации карточки: %s", e, exc_info=True)
        await message.reply_text(
            "⚠️ Произошла ошибка при генерации. Попробуйте позже.",
            reply_markup=kb_main(),
        )
    finally:
        clear_draft(ctx)

    return MAIN_MENU
