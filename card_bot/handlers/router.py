"""
handlers/router.py — Сборка ConversationHandler и Application.

Здесь только маршрутизация: какое состояние → какой хэндлер.
Никакой бизнес-логики.
"""

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

from config import (
    BOT_TOKEN,
    # Состояния
    REGISTER_NAME, REGISTER_AGE, MAIN_MENU, CARD_MENU,
    TEMPLATE_SELECT_TYPE, TEMPLATE_ORG_NAME, TEMPLATE_HOLDER_NAME,
    TEMPLATE_POSITION, TEMPLATE_PHONE, TEMPLATE_EMAIL, TEMPLATE_WEBSITE,
    TEMPLATE_CARD_NUMBER, TEMPLATE_ACCESS_LEVEL, TEMPLATE_MEMBER_TYPE,
    TEMPLATE_VALIDITY, TEMPLATE_ADDITIONAL, TEMPLATE_SAVE_NAME,
    TEMPLATE_REVIEW, TEMPLATE_CONFIRM_APPLY,
    SELECT_SAVED_TEMPLATE, CONFIRM_USE_TEMPLATE,
    # Кнопки
    BTN_PROFILE, BTN_GENERATE, BTN_HELP,
    BTN_CREATE_TPL, BTN_USE_TPL, BTN_BACK, BTN_CANCEL,
)

# Хэндлеры по модулям
from handlers.registration import cmd_start, handle_name, handle_age
from handlers.menu import (
    handle_profile, handle_help, handle_generate_menu,
    handle_back_to_main, cmd_cancel, error_handler,
)
from handlers.template_create import (
    handle_create_template, cbq_select_type,
    handle_org_name, handle_holder_name,
    handle_position, handle_phone, handle_email, handle_website,
    handle_card_number, handle_access_level, handle_member_type,
    handle_validity, handle_additional, handle_save_name,
    handle_template_review, cbq_apply_yes, cbq_apply_no,
)
from handlers.template_use import (
    handle_use_template, cbq_template_selected,
    cbq_use_yes, cbq_use_no,
)


def build_conversation() -> ConversationHandler:
    """Собирает ConversationHandler со всеми состояниями бота."""
    return ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={

            # ── Регистрация ─────────────────────────────────────────────────────
            REGISTER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name),
            ],
            REGISTER_AGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_age),
            ],

            # ── Главное меню ────────────────────────────────────────────────────
            MAIN_MENU: [
                MessageHandler(filters.Regex(f"^{BTN_PROFILE}$"),  handle_profile),
                MessageHandler(filters.Regex(f"^{BTN_GENERATE}$"), handle_generate_menu),
                MessageHandler(filters.Regex(f"^{BTN_HELP}$"),     handle_help),
            ],

            # ── Подменю карточек ────────────────────────────────────────────────
            CARD_MENU: [
                MessageHandler(filters.Regex(f"^{BTN_CREATE_TPL}$"), handle_create_template),
                MessageHandler(filters.Regex(f"^{BTN_USE_TPL}$"),    handle_use_template),
                MessageHandler(filters.Regex(f"^{BTN_BACK}$"),       handle_back_to_main),
            ],

            # ── Создание шаблона ────────────────────────────────────────────────
            TEMPLATE_SELECT_TYPE: [
                CallbackQueryHandler(cbq_select_type, pattern="^(ctype_|cancel)"),
            ],
            TEMPLATE_ORG_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_org_name),
            ],
            TEMPLATE_HOLDER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_holder_name),
            ],
            TEMPLATE_POSITION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_position),
            ],
            TEMPLATE_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone),
            ],
            TEMPLATE_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email),
            ],
            TEMPLATE_WEBSITE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_website),
            ],
            TEMPLATE_CARD_NUMBER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_card_number),
            ],
            TEMPLATE_ACCESS_LEVEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_access_level),
            ],
            TEMPLATE_MEMBER_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_member_type),
            ],
            TEMPLATE_VALIDITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_validity),
            ],
            TEMPLATE_ADDITIONAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_additional),
            ],
            TEMPLATE_SAVE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_save_name),
            ],
            TEMPLATE_REVIEW: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_template_review),
            ],
            TEMPLATE_CONFIRM_APPLY: [
                CallbackQueryHandler(cbq_apply_yes, pattern="^apply_yes$"),
                CallbackQueryHandler(cbq_apply_no,  pattern="^apply_no$"),
            ],

            # ── Использование шаблона ───────────────────────────────────────────
            SELECT_SAVED_TEMPLATE: [
                CallbackQueryHandler(cbq_template_selected, pattern="^(tpl_|cancel)"),
            ],
            CONFIRM_USE_TEMPLATE: [
                CallbackQueryHandler(cbq_use_yes, pattern="^use_yes$"),
                CallbackQueryHandler(cbq_use_no,  pattern="^use_no$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cmd_cancel),
            CommandHandler("start",  cmd_start),
            MessageHandler(filters.Regex(f"^{BTN_CANCEL}$"), cmd_cancel),
        ],
        allow_reentry=True,
        name="main_conversation",
        persistent=False,
    )


def build_application() -> Application:
    """Создаёт Application, регистрирует ConversationHandler и error_handler."""
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(build_conversation())
    app.add_error_handler(error_handler)
    return app
