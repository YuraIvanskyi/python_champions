"""Quest-style feedback cards for Code Coach."""

from __future__ import annotations

from typing import Any

import pygame

from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font, title_font

_CARD_PAD_X = 12
_CARD_PAD_Y = 6
_RIBBON_H = 22
_TITLE_PT = 15
_BODY_PT = 13


def quest_card_height(item: dict[str, Any], width: int) -> int:
    return 104


def draw_quest_card(
    surface: pygame.Surface,
    rect: pygame.Rect,
    item: dict[str, Any],
    *,
    selected: bool = False,
) -> None:
    panel = str(item.get("panel", "parchment"))
    skin.draw_panel(surface, rect, style=panel)  # type: ignore[arg-type]

    if selected:
        pygame.draw.rect(surface, colors.TEAL_ACCENT, rect, 2, border_radius=6)

    category = str(item.get("category", "style"))

    # Category ribbon — fits inside card with padding
    ribbon = pygame.Rect(
        rect.x + _CARD_PAD_X,
        rect.y + _CARD_PAD_Y,
        min(rect.width - _CARD_PAD_X * 2, 110),
        _RIBBON_H,
    )
    skin.draw_category_ribbon(surface, ribbon, category=category)

    # Category label inside ribbon — clipped
    # Praise uses dark text on bright emerald; others use white
    if category == "praise":
        cat_color = (18, 72, 36)     # dark forest green — high contrast on emerald
    elif category in ("efficiency", "runtime"):
        cat_color = (255, 255, 255)
    else:
        cat_color = (255, 240, 200)
    cat_font = body_font(_BODY_PT - 1)
    skin.draw_text_clipped(
        surface,
        category.upper(),
        ribbon,
        cat_font,
        cat_color,
        align="center",
        pad_x=6,
    )

    # Title — right of ribbon, or below if ribbon takes full width
    title_x = ribbon.right + 8
    title_available_w = rect.right - _CARD_PAD_X - title_x
    title_font_obj = title_font(_TITLE_PT)
    title_text = str(item.get("title", "Tip"))
    title_color = colors.GOLD_TEXT if panel != "parchment" else colors.PARCHMENT_TEXT

    if title_available_w >= 40:
        title_rect = pygame.Rect(title_x, rect.y + _CARD_PAD_Y, title_available_w, _RIBBON_H)
        skin.draw_text_clipped(surface, title_text, title_rect, title_font_obj, title_color, align="left", pad_y=2)
    else:
        # Place title below ribbon
        title_rect = pygame.Rect(
            rect.x + _CARD_PAD_X, ribbon.bottom + 2,
            rect.width - _CARD_PAD_X * 2, _TITLE_PT + 4,
        )
        skin.draw_text_clipped(surface, title_text, title_rect, title_font_obj, title_color, align="left")

    # Message — below ribbon row
    msg_y = rect.y + _CARD_PAD_Y + _RIBBON_H + 4
    msg_rect = pygame.Rect(rect.x + _CARD_PAD_X, msg_y, rect.width - _CARD_PAD_X * 2, _BODY_PT + 6)
    body_color = colors.TEXT_BODY if panel != "parchment" else colors.PARCHMENT_TEXT
    body_font_obj = body_font(_BODY_PT)
    skin.draw_text_clipped(
        surface,
        str(item.get("message", "")),
        msg_rect,
        body_font_obj,
        body_color,
        align="left",
    )

    # Fix hint — near bottom
    fix = str(item.get("fix_hint", ""))
    if fix:
        fix_y = msg_y + _BODY_PT + 8
        fix_rect = pygame.Rect(rect.x + _CARD_PAD_X, fix_y, rect.width - _CARD_PAD_X * 2, _BODY_PT + 6)
        fix_color = colors.GOLD_TEXT if selected else colors.TEXT_MUTED
        skin.draw_text_clipped(
            surface,
            f"Quest: {fix}",
            fix_rect,
            body_font_obj,
            fix_color,
            align="left",
        )
