"""
ai_generator.py – Google Gemini integration for card content generation.
Returns structured JSON that card_renderer can consume.
"""

import json
import logging
import re
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL, CARD_TYPE_LABELS

logger = logging.getLogger(__name__)


def _init_gemini() -> genai.GenerativeModel | None:
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set")
        return None
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        generation_config=genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=1024,
        ),
    )


_model: genai.GenerativeModel | None = None


def get_model() -> genai.GenerativeModel | None:
    global _model
    if _model is None:
        _model = _init_gemini()
    return _model


def _build_prompt(template: dict) -> str:
    card_type_name = CARD_TYPE_LABELS.get(template.get("card_type", ""), "Карта")

    fields_text = "\n".join([
        f"- Тип карты: {card_type_name}",
        f"- Организация: {template.get('org_name', '')}",
        f"- Владелец: {template.get('holder_name', '')}",
        f"- Должность: {template.get('position', '') or 'не указана'}",
        f"- Телефон: {template.get('phone', '') or 'не указан'}",
        f"- Email: {template.get('email', '') or 'не указан'}",
        f"- Сайт: {template.get('website', '') or 'не указан'}",
        f"- Номер карты: {template.get('card_number', '') or 'авто'}",
        f"- Уровень доступа: {template.get('access_level', '') or 'стандарт'}",
        f"- Тип членства: {template.get('membership_type', '') or 'не указан'}",
        f"- Срок действия: {template.get('validity_date', '') or 'бессрочно'}",
        f"- Дополнительно: {template.get('additional_info', '') or 'нет'}",
    ])

    return f"""Ты — профессиональный дизайнер карточек. 
На основе данных ниже создай оформление карточки и верни ТОЛЬКО JSON (без markdown, без ```json```).

Данные:
{fields_text}

Верни JSON строго в этом формате:
{{
  "headline": "Краткое название/заголовок карточки (максимум 25 символов)",
  "tagline": "Подзаголовок или слоган организации (максимум 40 символов)",
  "holder_display": "Имя владельца для отображения",
  "detail_lines": [
    {{"label": "Метка", "value": "Значение"}}
  ],
  "card_number_display": "Форматированный номер карты (например ACC·2024·0001 или AUTO если не указан, генерируй красивый)",
  "validity_display": "Срок действия для отображения",
  "footer_note": "Краткое примечание в нижней части (максимум 50 символов)",
  "colors": {{
    "bg_top": "#hexcolor — тёмный верх градиента",
    "bg_bottom": "#hexcolor — чуть светлее низ",
    "accent": "#hexcolor — яркий акцентный цвет",
    "text_primary": "#hexcolor — цвет основного текста",
    "text_secondary": "#hexcolor — цвет второстепенного текста"
  }}
}}

Цветовые рекомендации по типу:
- Пропускная карта: тёмно-синий/тёмно-серый с синим или красным акцентом
- Карта членства: тёмно-фиолетовый или тёмно-зелёный с золотым акцентом
- Визитка: угольный или белый с фирменным акцентом

Верни ТОЛЬКО JSON, без пояснений."""


def _extract_json(text: str) -> dict:
    """Extract JSON from raw AI response."""
    text = text.strip()
    # Remove markdown code fences if present
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    return json.loads(text)


async def generate_card_content(template: dict) -> dict:
    """
    Call Gemini and return structured card data dict.
    Returns a fallback dict if AI is unavailable or fails.
    """
    model = get_model()
    if model is None:
        return _fallback_content(template)

    prompt = _build_prompt(template)
    try:
        response = await model.generate_content_async(prompt)
        data = _extract_json(response.text)
        logger.info("✅ Gemini generated card content successfully")
        return data
    except json.JSONDecodeError as e:
        logger.error("JSON parse error from Gemini: %s\nRaw: %s", e, getattr(response, "text", ""))
        return _fallback_content(template)
    except Exception as e:
        logger.error("Gemini error: %s", e)
        return _fallback_content(template)


def _fallback_content(template: dict) -> dict:
    """Return a basic card content dict when AI is unavailable."""
    from config import CARD_TYPE_LABELS, CARD_PASS, CARD_MEMBERSHIP
    card_type = template.get("card_type", "")
    colors = {
        CARD_PASS:       {"bg_top": "#0D1B2A", "bg_bottom": "#1B2D44", "accent": "#00B4D8",
                          "text_primary": "#FFFFFF", "text_secondary": "#90CAF9"},
        CARD_MEMBERSHIP: {"bg_top": "#1A0533", "bg_bottom": "#2D1B4E", "accent": "#FFD700",
                          "text_primary": "#FFFFFF", "text_secondary": "#E1BEE7"},
    }.get(card_type, {"bg_top": "#1A1A2E", "bg_bottom": "#2C2C44", "accent": "#3498DB",
                      "text_primary": "#FFFFFF", "text_secondary": "#B0BEC5"})

    details = []
    if template.get("position"):
        details.append({"label": "Должность", "value": template["position"]})
    if template.get("phone"):
        details.append({"label": "Телефон", "value": template["phone"]})
    if template.get("email"):
        details.append({"label": "Email", "value": template["email"]})
    if template.get("access_level"):
        details.append({"label": "Доступ", "value": template["access_level"]})
    if template.get("membership_type"):
        details.append({"label": "Членство", "value": template["membership_type"]})

    return {
        "headline": CARD_TYPE_LABELS.get(card_type, "Карта"),
        "tagline": template.get("org_name", ""),
        "holder_display": template.get("holder_name", ""),
        "detail_lines": details,
        "card_number_display": template.get("card_number") or "AUTO·0001",
        "validity_display": template.get("validity_date") or "Бессрочно",
        "footer_note": template.get("additional_info") or template.get("org_name", ""),
        "colors": colors,
    }
