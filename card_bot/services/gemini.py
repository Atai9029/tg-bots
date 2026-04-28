from __future__ import annotations

import json
from typing import Any

from config import settings


def _fallback_payload(data: dict[str, Any]) -> dict[str, str]:
    title = data.get("organization") or data.get("name") or "Карточка"
    return {
        "headline": title,
        "subtitle": data.get("card_type", "Визитка / пропуск / членство"),
        "body": " ".join(filter(None, [data.get("full_name", ""), data.get("position", ""), data.get("phone", ""), data.get("email", "")]))[:240],
    }


async def polish_card_text(data: dict[str, Any]) -> dict[str, str]:
    if not settings.google_api_key:
        return _fallback_payload(data)

    try:
        from google import genai

        client = genai.Client(api_key=settings.google_api_key)
        prompt = f"""
Ты помощник для генерации текста карточек. Верни ТОЛЬКО JSON без markdown.
Нужно заполнить поля:
headline, subtitle, body.
Данные пользователя:
{json.dumps(data, ensure_ascii=False, indent=2)}

Сделай текст коротким, деловым и красивым для карточки.
"""
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        text = (response.text or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            text = text.replace("json\n", "", 1).strip()
        payload = json.loads(text)
        return {
            "headline": str(payload.get("headline", _fallback_payload(data)["headline"])),
            "subtitle": str(payload.get("subtitle", _fallback_payload(data)["subtitle"])),
            "body": str(payload.get("body", _fallback_payload(data)["body"])),
        }
    except Exception:
        return _fallback_payload(data)
