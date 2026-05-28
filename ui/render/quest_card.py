"""Quest-style feedback cards for Code Coach."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pygame

from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font, title_font

_CARD_PAD_X     = 16
_CARD_PAD_Y     = 10
_RIBBON_H       = 22
_TITLE_PT       = 15
_BODY_PT        = 13
_LINE_H         = _BODY_PT + 4   # pixel height per wrapped line
_MAX_MSG_LINES  = 5
_MAX_HINT_LINES = 2
_SCORE_MENTOR_GAP = 10
_MENTOR2_PATH = Path(__file__).resolve().parents[1] / "assets" / "icons" / "mentor_2.png"
_MENTOR2_CACHE: dict[int, pygame.Surface | None] = {}


# ── Text helpers ──────────────────────────────────────────────────────────────

def _wrap_text(text: str, font: pygame.font.Font, max_w: int) -> list[str]:
    """Word-wrap *text* so each line fits within *max_w* pixels."""
    if not text:
        return [""]
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = (current + " " + word).strip() if current else word
        if font.size(trial)[0] <= max_w:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _draw_wrapped(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    x: int,
    y: int,
    max_w: int,
    max_lines: int = 2,
) -> int:
    """Blit word-wrapped text; returns the y coordinate after the last line."""
    lines = _wrap_text(text, font, max_w)[:max_lines]
    for line in lines:
        surf = font.render(line, True, color)
        surface.blit(surf, (x, y))
        y += _LINE_H
    return y


# ── Score summary card ────────────────────────────────────────────────────────

def _mentor2_surface(max_height: int) -> pygame.Surface | None:
    if max_height in _MENTOR2_CACHE:
        return _MENTOR2_CACHE[max_height]
    if not _MENTOR2_PATH.is_file():
        _MENTOR2_CACHE[max_height] = None
        return None
    try:
        image = pygame.image.load(str(_MENTOR2_PATH))
        if pygame.display.get_surface() is not None:
            image = image.convert_alpha()
        src_w, src_h = image.get_size()
        if src_h <= 0:
            _MENTOR2_CACHE[max_height] = None
            return None
        display_h = min(max_height, src_h)
        display_w = max(1, int(display_h * src_w / src_h))
        scaled = pygame.transform.smoothscale(image, (display_w, display_h))
        _MENTOR2_CACHE[max_height] = scaled
        return scaled
    except pygame.error:
        _MENTOR2_CACHE[max_height] = None
        return None


def score_card_text_column(rect: pygame.Rect) -> tuple[int, int]:
    """Return (text_x, text_width) for the score card content beside mentor_2."""
    pad_x = 12
    inner_h = max(1, rect.height - 8 * 2)
    mentor = _mentor2_surface(inner_h)
    if mentor is None:
        return rect.x + pad_x, rect.width - pad_x * 2
    text_x = rect.x + pad_x + mentor.get_width() + _SCORE_MENTOR_GAP
    text_w = max(80, rect.right - pad_x - text_x)
    return text_x, text_w


def draw_score_card(
    surface: pygame.Surface,
    rect: pygame.Rect,
    bot_name: str,
    gameplay_score: object,
    code_score: object,
    final_score: object,
    *,
    lang: str = "en",
) -> None:
    """Draw the score summary at the top of the quest column."""
    skin.draw_panel(surface, rect, style="parchment")

    pad_x, pad_y = 12, 8
    inner_h = max(1, rect.height - pad_y * 2)
    mentor = _mentor2_surface(inner_h)
    text_x, text_w = score_card_text_column(rect)

    if mentor is not None:
        mentor_x = rect.x + pad_x
        mentor_y = rect.y + pad_y + (inner_h - mentor.get_height()) // 2
        surface.blit(mentor, (mentor_x, mentor_y))

    from engine.i18n import translate

    greeting = translate("quest.greeting", lang=lang, name=bot_name)
    greeting_font = body_font(14)
    greeting_lines = _wrap_text(greeting, greeting_font, text_w)[:2]
    y = rect.y + pad_y
    for line in greeting_lines:
        skin.draw_text_clipped(
            surface,
            line,
            pygame.Rect(text_x, y, text_w, greeting_font.get_height() + 2),
            greeting_font,
            colors.PARCHMENT_TEXT,
            align="left",
        )
        y += greeting_font.get_height() + 2

    score_top = y + 4
    score_bottom = rect.bottom - pad_y
    avail_h = max(24, score_bottom - score_top)
    col_w = max(36, text_w // 3)

    val_font = title_font(16)
    lbl_font = body_font(11)

    entries: list[tuple[str, str, tuple[int, int, int]]] = [
        (translate("quest.gameplay", lang=lang), str(gameplay_score), colors.PARCHMENT_TEXT),
        (translate("quest.code", lang=lang), str(code_score), colors.PARCHMENT_TEXT),
        (translate("quest.final", lang=lang), str(final_score), (165, 88, 18)),
    ]

    for i, (label, val, color) in enumerate(entries):
        cx = text_x + col_w * i + col_w // 2
        val_surf = val_font.render(val, True, color)
        lbl_surf = lbl_font.render(label, True, colors.PARCHMENT_EDGE)
        block_h = val_surf.get_height() + 2 + lbl_surf.get_height()
        base_y = score_top + max(0, (avail_h - block_h) // 2)
        surface.blit(val_surf, (cx - val_surf.get_width() // 2, base_y))
        surface.blit(
            lbl_surf,
            (cx - lbl_surf.get_width() // 2, base_y + val_surf.get_height() + 2),
        )

    sep_top = score_top + 2
    sep_bot = score_bottom - 2
    for i in (1, 2):
        sx = text_x + col_w * i
        pygame.draw.line(surface, colors.PARCHMENT_EDGE, (sx, sep_top), (sx, sep_bot))


# ── Feedback quest card ───────────────────────────────────────────────────────

def quest_card_height(item: dict[str, Any], width: int) -> int:
    """Return the pixel height needed for this card at the given width."""
    inner_w = max(1, width - _CARD_PAD_X * 2)
    font = body_font(_BODY_PT)
    msg_lines = min(
        _MAX_MSG_LINES,
        len(_wrap_text(str(item.get("message", "")), font, inner_w)),
    )
    hint = str(item.get("fix_hint", ""))
    hint_lines = (
        min(_MAX_HINT_LINES, len(_wrap_text(f"Quest: {hint}", font, inner_w)))
        if hint else 0
    )
    h  = _CARD_PAD_Y + _RIBBON_H + 5   # top pad + ribbon row + gap below ribbon
    h += msg_lines * _LINE_H
    if hint_lines:
        h += 4 + hint_lines * _LINE_H
    h += _CARD_PAD_Y                    # bottom padding
    return max(72, h)


def draw_quest_card(
    surface: pygame.Surface,
    rect: pygame.Rect,
    item: dict[str, Any],
    *,
    selected: bool = False,
    lang: str = "en",
) -> None:
    panel       = str(item.get("panel", "parchment"))
    is_parchment = panel == "parchment"
    skin.draw_panel(surface, rect, style=panel)  # type: ignore[arg-type]

    if selected:
        pygame.draw.rect(surface, colors.TEAL_ACCENT, rect, 2, border_radius=6)

    from engine.i18n import category_label, translate

    category = str(item.get("category", "style"))
    category_text = category_label(category, lang)

    # ── Category ribbon ───────────────────────────────────────────────────────
    ribbon = pygame.Rect(
        rect.x + _CARD_PAD_X,
        rect.y + _CARD_PAD_Y,
        min(rect.width - _CARD_PAD_X * 2, 110),
        _RIBBON_H,
    )
    skin.draw_category_ribbon(surface, ribbon, category=category)

    # Label inside the ribbon
    if category == "praise":
        cat_color = (18, 72, 36)
    elif category in ("efficiency", "runtime"):
        cat_color = (255, 255, 255)
    else:
        cat_color = (255, 240, 200)
    cat_font = body_font(_BODY_PT - 1)
    skin.draw_text_clipped(
        surface, category_text, ribbon, cat_font, cat_color,
        align="center", pad_x=6,
    )

    # ── Title — right of ribbon ───────────────────────────────────────────────
    title_x         = ribbon.right + 8
    title_avail_w   = rect.right - _CARD_PAD_X - title_x
    title_font_obj  = title_font(_TITLE_PT)
    title_text      = str(item.get("title", translate("quest.tip", lang=lang)))
    # Use dark ink on parchment; gold on dark (stone/wood) panels
    title_color = colors.PARCHMENT_TEXT if is_parchment else colors.GOLD_TEXT

    if title_avail_w >= 40:
        title_rect = pygame.Rect(title_x, rect.y + _CARD_PAD_Y, title_avail_w, _RIBBON_H)
        skin.draw_text_clipped(
            surface, title_text, title_rect, title_font_obj, title_color,
            align="left", pad_y=2,
        )
    else:
        title_rect = pygame.Rect(
            rect.x + _CARD_PAD_X, ribbon.bottom + 2,
            rect.width - _CARD_PAD_X * 2, _TITLE_PT + 4,
        )
        skin.draw_text_clipped(
            surface, title_text, title_rect, title_font_obj, title_color,
            align="left",
        )

    # ── Message — word-wrapped, up to 2 lines ────────────────────────────────
    body_font_obj = body_font(_BODY_PT)
    body_color    = colors.PARCHMENT_TEXT if is_parchment else colors.TEXT_BODY
    msg_x         = rect.x + _CARD_PAD_X
    msg_w         = rect.width - _CARD_PAD_X * 2
    msg_y         = rect.y + _CARD_PAD_Y + _RIBBON_H + 5

    # Clip to the intersection of the card rect and whatever outer clip is active
    # (the outer clip is the scrollable panel viewport — we must not widen it).
    old_clip = surface.get_clip()
    active_clip = old_clip.clip(rect) if old_clip.width > 0 and old_clip.height > 0 else rect
    surface.set_clip(active_clip)

    after_msg_y = _draw_wrapped(
        surface, str(item.get("message", "")),
        body_font_obj, body_color, msg_x, msg_y, msg_w, max_lines=_MAX_MSG_LINES,
    )

    # ── Fix hint — readable colour on every background ────────────────────────
    fix = str(item.get("fix_hint", ""))
    if fix:
        fix_y = after_msg_y + 4
        if is_parchment:
            fix_color: tuple[int, int, int] = (118, 82, 28)
        else:
            fix_color = colors.GOLD_TEXT if selected else colors.TEXT_MUTED
        _draw_wrapped(
            surface, translate("quest.quest_prefix", lang=lang, hint=fix),
            body_font_obj, fix_color, msg_x, fix_y, msg_w, max_lines=_MAX_HINT_LINES,
        )

    surface.set_clip(old_clip)
