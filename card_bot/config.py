import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Tokens ────────────────────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

# ─── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATABASE_PATH = BASE_DIR / "data" / "bot.db"
CARDS_DIR = BASE_DIR / "data" / "cards"

# Create directories on import
DATABASE_PATH.parent.mkdir(exist_ok=True)
CARDS_DIR.mkdir(exist_ok=True)

# ─── Fonts ─────────────────────────────────────────────────────────────────────
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

# ─── Conversation States ────────────────────────────────────────────────────────
(
    REGISTER_NAME,          # 0
    REGISTER_AGE,           # 1
    MAIN_MENU,              # 2
    CARD_MENU,              # 3
    TEMPLATE_SELECT_TYPE,   # 4
    TEMPLATE_ORG_NAME,      # 5
    TEMPLATE_HOLDER_NAME,   # 6
    TEMPLATE_POSITION,      # 7  (business card)
    TEMPLATE_PHONE,         # 8
    TEMPLATE_EMAIL,         # 9
    TEMPLATE_WEBSITE,       # 10
    TEMPLATE_CARD_NUMBER,   # 11
    TEMPLATE_ACCESS_LEVEL,  # 12 (pass card)
    TEMPLATE_MEMBER_TYPE,   # 13 (membership card)
    TEMPLATE_VALIDITY,      # 14
    TEMPLATE_ADDITIONAL,    # 15
    TEMPLATE_SAVE_NAME,     # 16
    TEMPLATE_REVIEW,        # 17  ← review before saving
    TEMPLATE_CONFIRM_APPLY, # 18
    SELECT_SAVED_TEMPLATE,  # 19
    CONFIRM_USE_TEMPLATE,   # 20
) = range(21)

# ─── Card Types ─────────────────────────────────────────────────────────────────
CARD_PASS = "pass"
CARD_MEMBERSHIP = "membership"
CARD_BUSINESS = "business"

CARD_TYPE_LABELS = {
    CARD_PASS: "🔐 Пропускная карта",
    CARD_MEMBERSHIP: "🎫 Карта членства",
    CARD_BUSINESS: "💼 Визитка",
}

# ─── Button Texts ───────────────────────────────────────────────────────────────
BTN_PROFILE       = "👤 Профиль"
BTN_GENERATE      = "🎴 Генерация карточек"
BTN_HELP          = "❓ Помощь"
BTN_CREATE_TPL    = "📝 Создать шаблон"
BTN_USE_TPL       = "📋 Использовать шаблон"
BTN_BACK          = "🔙 Назад"
BTN_CANCEL        = "❌ Отмена"
BTN_SKIP          = "⏭ Пропустить"
BTN_FINISH        = "✅ Завершить шаблон"

# ─── AI Model ──────────────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-1.5-flash"

# ─── Card Image Size (Credit-card ratio 85.6 × 53.98 mm → ×10) ────────────────
CARD_W = 856
CARD_H = 540
