"""Quest-style feedback cards for Code Coach."""

from __future__ import annotations

from typing import Any

import pygame

from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font, title_font

_CARD_PAD_X = 16
_CARD_PAD_Y = 10
_RIBBON_H   = 22
_TITLE_PT   = 15
_BODY_PT    = 13
_LINE_H     = _BODY_PT + 4   # pixel height per wrapped line


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

def draw_score_card(
    surface: pygame.Surface,
    rect: pygame.Rect,
    bot_name: str,
    gameplay_score: object,
    code_score: object,
    final_score: object,
) -> None:
    """Draw the prominent score summary at the top of the quest column.

    Shows three equally-spaced score columns (Gameplay / Code / Final) with
    the bot name in a header row, all on a parchment panel.
    """
    skin.draw_panel(surface, rect, style="parchment")

    pad_x, pad_y = 16, 10
    inner_x = rect.x + pad_x
    inner_w  = rect.width - pad_x * 2

    # ── Row 1: "RESULTS" ribbon  +  bot name ─────────────────────────────────
    ribbon_h = 20
    ribbon_w = min(82, inner_w // 3)
    ribbon_rect = pygame.Rect(inner_x, rect.y + pad_y, ribbon_w, ribbon_h)
    skin.draw_category_ribbon(surface, ribbon_rect, category="praise")
    lbl_font = body_font(_BODY_PT - 1)
    skin.draw_text_clipped(
        surface, "RESULTS", ribbon_rect, lbl_font, (18, 72, 36),
        align="center", pad_x=4,
    )

    # Bot name to the right of the ribbon
    name_x = inner_x + ribbon_w + 8
    name_avail = rect.right - pad_x - name_x
    name_rect  = pygame.Rect(name_x, rect.y + pad_y, name_avail, ribbon_h)
    name_font  = title_font(_TITLE_PT)
    skin.draw_text_clipped(
        surface, bot_name, name_rect, name_font, colors.PARCHMENT_TEXT,
        align="left",
    )

    # ── Divider ───────────────────────────────────────────────────────────────
    div_y = rect.y + pad_y + ribbon_h + 6
    pygame.draw.line(
        surface, colors.PARCHMENT_EDGE,
        (inner_x + 6, div_y), (rect.right - pad_x - 6, div_y),
    )

    # ── Three score columns ───────────────────────────────────────────────────
    col_y   = div_y + 7
    avail_h = rect.bottom - pad_y - col_y
    col_w   = inner_w // 3

    val_font = title_font(18)
    lbl_font_sm = body_font(_BODY_PT - 1)

    # Final score gets a warm amber to stand out; others use dark parchment ink
    entries: list[tuple[str, str, tuple[int, int, int]]] = [
        ("Gameplay", str(gameplay_score), colors.PARCHMENT_TEXT),
        ("Code",     str(code_score),     colors.PARCHMENT_TEXT),
        ("Final",    str(final_score),    (165, 88, 18)),
    ]

    for i, (label, val, color) in enumerate(entries):
        cx = inner_x + col_w * i + col_w // 2

        val_surf = val_font.render(val, True, color)
        lbl_surf = lbl_font_sm.render(label, True, colors.PARCHMENT_EDGE)

        block_h = val_surf.get_height() + 3 + lbl_surf.get_height()
        base_y  = col_y + max(0, (avail_h - block_h) // 2)

        surface.blit(val_surf, (cx - val_surf.get_width() // 2, base_y))
        surface.blit(lbl_surf, (
            cx - lbl_surf.get_width() // 2,
            base_y + val_surf.get_height() + 3,
        ))

    # Vertical separators between the three columns
    sep_top = col_y + 4
    sep_bot = rect.bottom - pad_y - 4
    for i in [1, 2]:
        sx = inner_x + col_w * i
        pygame.draw.line(surface, colors.PARCHMENT_EDGE, (sx, sep_top), (sx, sep_bot))


# ── Feedback quest card ───────────────────────────────────────────────────────

def quest_card_height(item: dict[str, Any], width: int) -> int:
    return 104


def draw_quest_card(
    surface: pygame.Surface,
    rect: pygame.Rect,
    item: dict[str, Any],
    *,
    selected: bool = False,
) -> None:
    panel       = str(item.get("panel", "parchment"))
    is_parchment = panel == "parchment"
    skin.draw_panel(surface, rect, style=panel)  # type: ignore[arg-type]

    if selected:
        pygame.draw.rect(surface, colors.TEAL_ACCENT, rect, 2, border_radius=6)

    category = str(item.get("category", "style"))

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
        surface, category.upper(), ribbon, cat_font, cat_color,
        align="center", pad_x=6,
    )

    # ── Title — right of ribbon ───────────────────────────────────────────────
    title_x         = ribbon.right + 8
    title_avail_w   = rect.right - _CARD_PAD_X - title_x
    title_font_obj  = title_font(_TITLE_PT)
    title_text      = str(item.get("title", "Tip"))
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
        body_font_obj, body_color, msg_x, msg_y, msg_w, max_lines=2,
    )

    # ── Fix hint — readable colour on every background ────────────────────────
    fix = str(item.get("fix_hint", ""))
    if fix:
        fix_y = after_msg_y + 4
        if is_parchment:
            # Muted amber-brown — high contrast on warm parchment, neither gold nor grey
            fix_color: tuple[int, int, int] = (118, 82, 28)
        else:
            fix_color = colors.GOLD_TEXT if selected else colors.TEXT_MUTED
        _draw_wrapped(
            surface, f"Quest: {fix}",
            body_font_obj, fix_color, msg_x, fix_y, msg_w, max_lines=1,
        )

    surface.set_clip(old_clip)
