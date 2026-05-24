"""Scrollable source panel with line highlights."""

from __future__ import annotations

import pygame

from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import code_font
from ui.widgets.scroll import ScrollState

LINE_HEIGHT = 18
_SCROLLBAR_W = 6


def draw_code_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    lines: list[str],
    highlight_lines: set[int],
    scroll: ScrollState,
    font_pt: int = 14,
) -> None:
    skin.draw_panel(surface, rect, style="stone")
    inner = rect.inflate(-10, -10)
    # Reserve right strip for the scrollbar so code never hides under it
    code_w = inner.width - _SCROLLBAR_W - 2
    font = code_font(font_pt)
    total_h = max(LINE_HEIGHT, len(lines) * LINE_HEIGHT)
    scroll.set_content(total_h, inner.height)

    clip = surface.get_clip()
    surface.set_clip(inner)
    y = inner.y - scroll.offset
    gutter_w = 36

    for index, text in enumerate(lines, start=1):
        line_rect = pygame.Rect(inner.x, y, code_w, LINE_HEIGHT)
        if line_rect.bottom < inner.top:
            y += LINE_HEIGHT
            continue
        if line_rect.top > inner.bottom:
            break
        if index in highlight_lines:
            hi = pygame.Rect(inner.x + gutter_w - 4, y, code_w - gutter_w + 4, LINE_HEIGHT)
            pygame.draw.rect(surface, (60, 100, 140), hi, border_radius=2)

        gutter_color = colors.TEAL_ACCENT if index in highlight_lines else colors.TEXT_MUTED
        num = font.render(str(index), True, gutter_color)
        surface.blit(num, (inner.x + 4, y + 1))

        color = colors.GOLD_TEXT if index in highlight_lines else colors.TEXT_BODY
        line_surf = font.render(text[:120] if len(text) > 120 else text, True, color)
        surface.blit(line_surf, (inner.x + gutter_w, y + 1))
        y += LINE_HEIGHT

    surface.set_clip(clip)

    # Scrollbar overlaid on the right edge of the inner area
    track = pygame.Rect(inner.right - _SCROLLBAR_W, inner.y, _SCROLLBAR_W, inner.height)
    skin.draw_scrollbar(
        surface, track,
        content_height=scroll.content_height,
        viewport_height=scroll.viewport_height,
        offset=scroll.offset,
    )
