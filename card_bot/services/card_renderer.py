from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _parse_colors(colors: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    mapping = {
        "dark": ((18, 20, 28), (240, 240, 245)),
        "light": ((245, 247, 250), (20, 24, 36)),
        "blue": ((16, 40, 77), (255, 255, 255)),
        "green": ((18, 63, 43), (255, 255, 255)),
        "red": ((77, 24, 24), (255, 255, 255)),
        "gold": ((64, 49, 15), (255, 248, 220)),
    }
    key = (colors or "").lower().strip()
    return mapping.get(key, mapping["dark"])


def render_card(data: dict[str, Any], ai_text: dict[str, str], output_path: str) -> str:
    bg, fg = _parse_colors(data.get("colors", "dark"))
    img = Image.new("RGB", (1600, 1000), bg)
    draw = ImageDraw.Draw(img)

    # Decorative blocks
    draw.rounded_rectangle((70, 70, 1530, 930), radius=48, outline=(255, 255, 255), width=2)
    light_block = tuple(min(255, c + 24) for c in bg)
    draw.rounded_rectangle((1050, 90, 1510, 300), radius=36, fill=light_block)
    draw.rounded_rectangle((1050, 335, 1510, 870), radius=36, fill=light_block)

    title_font = _font(80, bold=True)
    sub_font = _font(42, bold=False)
    body_font = _font(34, bold=False)
    small_font = _font(28, bold=False)

    draw.text((120, 120), ai_text.get("headline", data.get("organization", "Карточка")), font=title_font, fill=fg)
    draw.text((120, 220), ai_text.get("subtitle", data.get("card_type", "Card")), font=sub_font, fill=fg)
    draw.line((120, 300, 940, 300), fill=fg, width=4)

    lines = [
        f"Имя: {data.get('full_name', '')}",
        f"Должность: {data.get('position', '')}",
        f"Телефон: {data.get('phone', '')}",
        f"Email: {data.get('email', '')}",
        f"Сайт: {data.get('website', '')}",
        f"Адрес: {data.get('address', '')}",
        f"Срок: {data.get('expiry', '')}",
    ]

    y = 345
    for line in lines:
        if line.endswith(": ") or line.endswith(":"):
            continue
        draw.text((120, y), line, font=body_font, fill=fg)
        y += 62

    notes = data.get("notes", "")
    slogan = data.get("slogan", "")
    footer = " | ".join([part for part in [slogan, notes] if part])
    if footer:
        draw.text((120, 760), footer[:120], font=small_font, fill=fg)

    draw.rounded_rectangle((1080, 110, 1480, 220), radius=30, outline=fg, width=2)
    draw.text((1120, 140), "QR / ID", font=_font(48, bold=True), fill=fg)
    draw.text((1080, 360), ai_text.get("body", ""), font=small_font, fill=fg, spacing=10)

    os = Path(output_path)
    os.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path
