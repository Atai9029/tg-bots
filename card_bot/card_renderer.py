"""
card_renderer.py – Renders a professional card image using Pillow.
Card size: 856 × 540 px (credit-card ratio).
"""

import io
import hashlib
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import qrcode

from config import CARD_W, CARD_H, CARDS_DIR, FONT_REGULAR, FONT_BOLD, FONT_MONO

logger = logging.getLogger(__name__)

# ─── Font Loader ────────────────────────────────────────────────────────────────

def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _fonts():
    return {
        "title":   _font(FONT_BOLD,    42),
        "tagline": _font(FONT_REGULAR, 22),
        "name":    _font(FONT_BOLD,    34),
        "detail":  _font(FONT_REGULAR, 20),
        "label":   _font(FONT_REGULAR, 16),
        "mono":    _font(FONT_MONO,    20),
        "small":   _font(FONT_REGULAR, 15),
    }


# ─── Colour Helpers ─────────────────────────────────────────────────────────────

def _hex(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _lerp_color(c1: tuple, c2: tuple, t: float) -> tuple[int, int, int]:
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


# ─── QR Code ────────────────────────────────────────────────────────────────────

def _make_qr(data: str, size: int = 110) -> Image.Image:
    qr = qrcode.QRCode(version=1, box_size=3, border=2,
                       error_correction=qrcode.constants.ERROR_CORRECT_L)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="white", back_color="transparent").convert("RGBA")
    img = img.resize((size, size), Image.LANCZOS)
    return img


# ─── Card Chip ──────────────────────────────────────────────────────────────────

def _draw_chip(draw: ImageDraw.ImageDraw, x: int, y: int, accent: tuple) -> None:
    """Draw a simplified SIM/chip rectangle."""
    w, h = 52, 38
    draw.rounded_rectangle([x, y, x + w, y + h], radius=5,
                            fill=(200, 175, 100), outline=(160, 140, 80), width=1)
    # Chip lines
    mid_y = y + h // 2
    for lx in [x + 8, x + 22, x + 36]:
        draw.line([(lx, y + 4), (lx, y + h - 4)], fill=(160, 140, 80), width=1)
    draw.line([(x + 4, mid_y), (x + w - 4, mid_y)], fill=(160, 140, 80), width=1)


# ─── Gradient Background ────────────────────────────────────────────────────────

def _draw_gradient_bg(img: Image.Image, top: tuple, bottom: tuple) -> None:
    draw = ImageDraw.Draw(img)
    for y in range(CARD_H):
        t = y / CARD_H
        color = _lerp_color(top, bottom, t)
        draw.line([(0, y), (CARD_W, y)], fill=color)


# ─── Rounded Card Mask ──────────────────────────────────────────────────────────

def _apply_rounded_mask(img: Image.Image, radius: int = 28) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, img.width, img.height], radius=radius, fill=255)
    result = img.convert("RGBA")
    result.putalpha(mask)
    return result


# ─── Main Renderer ──────────────────────────────────────────────────────────────

def render_card(template: dict, ai: dict) -> Path:
    """
    Render a card image, save it to CARDS_DIR, return the Path.
    """
    colors = ai.get("colors", {})
    bg_top    = _hex(colors.get("bg_top",    "#0D1B2A"))
    bg_bottom = _hex(colors.get("bg_bottom", "#1B2D44"))
    accent    = _hex(colors.get("accent",    "#00B4D8"))
    text_pri  = _hex(colors.get("text_primary",   "#FFFFFF"))
    text_sec  = _hex(colors.get("text_secondary", "#90CAF9"))

    img  = Image.new("RGB", (CARD_W, CARD_H))
    _draw_gradient_bg(img, bg_top, bg_bottom)
    draw = ImageDraw.Draw(img)
    f    = _fonts()

    # ── Accent stripe at top ────────────────────────────────────────────────────
    stripe_h = 8
    draw.rectangle([0, 0, CARD_W, stripe_h], fill=accent)

    # ── Top-left: Organisation / Headline ───────────────────────────────────────
    headline = ai.get("headline", "Карточка")
    tagline  = ai.get("tagline",  "")
    draw.text((36, 30), headline, font=f["title"], fill=text_pri)
    if tagline:
        draw.text((38, 82), tagline, font=f["tagline"], fill=text_sec)

    # ── Card type badge (top-right) ─────────────────────────────────────────────
    from config import CARD_TYPE_LABELS
    badge_text = CARD_TYPE_LABELS.get(template.get("card_type", ""), "")
    if badge_text:
        bbox = draw.textbbox((0, 0), badge_text, font=f["small"])
        bw = bbox[2] - bbox[0] + 24
        bh = bbox[3] - bbox[1] + 12
        bx, by = CARD_W - bw - 28, 22
        draw.rounded_rectangle([bx, by, bx + bw, by + bh],
                                radius=6, fill=(*accent, 180))
        draw.text((bx + 12, by + 6), badge_text, font=f["small"], fill=text_pri)

    # ── Divider line ────────────────────────────────────────────────────────────
    div_y = 118
    draw.line([(36, div_y), (CARD_W - 36, div_y)], fill=(*accent, 100), width=1)

    # ── Chip (pass / membership) ─────────────────────────────────────────────────
    from config import CARD_PASS, CARD_MEMBERSHIP
    if template.get("card_type") in (CARD_PASS, CARD_MEMBERSHIP):
        _draw_chip(draw, 36, div_y + 20, accent)

    # ── Holder name ──────────────────────────────────────────────────────────────
    holder = ai.get("holder_display") or template.get("holder_name", "")
    name_y = div_y + 80
    draw.text((36, name_y), holder, font=f["name"], fill=text_pri)

    # ── Detail lines ─────────────────────────────────────────────────────────────
    details = ai.get("detail_lines", [])
    detail_x = 36
    detail_y = name_y + 50
    line_gap  = 28

    for item in details[:5]:
        label = item.get("label", "")
        value = item.get("value", "")
        if not value:
            continue
        draw.text((detail_x, detail_y),
                  f"{label}: ", font=f["label"], fill=text_sec)
        lw = draw.textbbox((0, 0), f"{label}: ", font=f["label"])[2]
        draw.text((detail_x + lw, detail_y),
                  str(value), font=f["detail"], fill=text_pri)
        detail_y += line_gap

    # ── QR code (right side) ─────────────────────────────────────────────────────
    qr_data = (
        f"Name:{holder}|Org:{template.get('org_name','')}|"
        f"Type:{template.get('card_type','')}|"
        f"Card:{ai.get('card_number_display','')}"
    )
    try:
        qr_img = _make_qr(qr_data, size=120)
        qr_x = CARD_W - 155
        qr_y = div_y + 15
        img.paste(qr_img, (qr_x, qr_y), qr_img)
    except Exception as e:
        logger.warning("QR generation failed: %s", e)

    # ── Bottom bar ───────────────────────────────────────────────────────────────
    bar_y = CARD_H - 72
    draw.rectangle([0, bar_y, CARD_W, CARD_H],
                   fill=(*_lerp_color(bg_bottom, (0, 0, 0), 0.3),))

    # Card number
    card_num = ai.get("card_number_display", "")
    draw.text((36, bar_y + 12), card_num, font=f["mono"], fill=text_sec)

    # Validity
    validity = ai.get("validity_display", "")
    if validity:
        label = "ДЕЙСТВИТЕЛЬНА ДО  "
        lw = draw.textbbox((0, 0), label, font=f["small"])[2]
        vx = CARD_W // 2
        draw.text((vx, bar_y + 8),  "ДЕЙСТВИТЕЛЬНА ДО", font=f["small"], fill=text_sec)
        draw.text((vx, bar_y + 26), validity,           font=f["detail"], fill=text_pri)

    # Footer note (right-aligned)
    footer = ai.get("footer_note", "")
    if footer:
        fb = draw.textbbox((0, 0), footer, font=f["small"])
        fw = fb[2] - fb[0]
        draw.text((CARD_W - fw - 28, bar_y + 18), footer, font=f["small"], fill=text_sec)

    # ── Apply rounded corners ────────────────────────────────────────────────────
    img = _apply_rounded_mask(img, radius=28)

    # ── Save ─────────────────────────────────────────────────────────────────────
    key = hashlib.md5(f"{template.get('id','x')}{holder}".encode()).hexdigest()[:12]
    out_path = CARDS_DIR / f"card_{key}.png"

    # Paste onto white background for final PNG
    final = Image.new("RGBA", img.size, (255, 255, 255, 255))
    final.paste(img, (0, 0), img)
    final.convert("RGB").save(out_path, "PNG", optimize=True)

    logger.info("Card saved → %s", out_path)
    return out_path


def render_card_bytes(template: dict, ai: dict) -> io.BytesIO:
    """Render card and return as BytesIO (no disk write)."""
    path = render_card(template, ai)
    buf = io.BytesIO(path.read_bytes())
    buf.seek(0)
    return buf
