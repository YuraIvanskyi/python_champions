"""Locale-aware button width from label metrics."""

from __future__ import annotations

from ui.skin.typography import body_font
from ui.widgets.controls import BUTTON_PAD_X


def button_width(
    label: str,
    *,
    font_size: int = 18,
    pad_x: int = BUTTON_PAD_X,
    icon: str | None = None,
    icon_size: int = 0,
    icon_gap: int = 6,
    min_width: int = 80,
) -> int:
    """Return pixel width that fits *label* without clipping."""
    font = body_font(font_size)
    text_w = font.size(label)[0]
    icon_extra = (icon_size + icon_gap) if icon else 0
    return max(min_width, text_w + pad_x * 2 + icon_extra)
