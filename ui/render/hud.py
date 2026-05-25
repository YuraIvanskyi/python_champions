"""Heads-up display text for simulation and replay."""

from __future__ import annotations

import pygame

from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font, title_font
from ui.theme import HUD_BODY_PT, HUD_TEXT_HEIGHT, HUD_TITLE_PT

_HUD_PAD_X = 16
_HUD_PAD_Y = 6
_HUD_TITLE_GAP = 2
_HUD_SUBTITLE_GAP = 4
_HUD_BODY_LINE = HUD_BODY_PT + 4


def draw_hud(
    surface: pygame.Surface,
    *,
    title: str,
    lines: list[str],
    subtitle: str = "",
    footer: str = "",
    y_offset: int | None = None,
    content_height: int | None = None,
) -> None:
    height = content_height if content_height is not None else HUD_TEXT_HEIGHT
    panel_top = y_offset if y_offset is not None else surface.get_height() - height
    panel = pygame.Rect(0, panel_top, surface.get_width(), height)
    skin.draw_panel(surface, panel, style="wood")
    pygame.draw.line(
        surface, (180, 148, 72),
        (0, panel_top), (surface.get_width(), panel_top), 2,
    )

    title_font_obj = title_font(HUD_TITLE_PT)
    body_font_obj = body_font(HUD_BODY_PT)
    inner = panel.inflate(-_HUD_PAD_X * 2, -_HUD_PAD_Y * 2)

    old_clip = surface.get_clip()
    surface.set_clip(panel)

    y = panel_top + _HUD_PAD_Y
    skin.draw_text_clipped(
        surface,
        title,
        pygame.Rect(_HUD_PAD_X, y, inner.width, HUD_TITLE_PT + 4),
        title_font_obj,
        colors.GOLD_TEXT,
        align="left",
    )
    y += HUD_TITLE_PT + _HUD_TITLE_GAP

    if subtitle:
        subtitle_font = body_font(max(HUD_BODY_PT - 2, 13))
        skin.draw_text_clipped(
            surface,
            subtitle,
            pygame.Rect(_HUD_PAD_X, y, inner.width, HUD_BODY_PT),
            subtitle_font,
            colors.TEXT_MUTED,
            align="left",
        )
        y += HUD_BODY_PT + _HUD_SUBTITLE_GAP

    for line in lines[:4]:
        if not line:
            continue
        skin.draw_text_clipped(
            surface,
            line,
            pygame.Rect(_HUD_PAD_X, y, inner.width, _HUD_BODY_LINE),
            body_font_obj,
            colors.TEXT_BODY,
            align="left",
        )
        y += _HUD_BODY_LINE

    if footer:
        skin.draw_text_clipped(
            surface,
            footer,
            pygame.Rect(
                _HUD_PAD_X,
                panel.bottom - _HUD_PAD_Y - HUD_BODY_PT,
                inner.width,
                HUD_BODY_PT,
            ),
            body_font_obj,
            colors.TEXT_MUTED,
            align="left",
        )

    surface.set_clip(old_clip)


def draw_toolbar_strip(surface: pygame.Surface, *, y: int, height: int) -> None:
    skin.draw_toolbar_strip(surface, y=y, height=height)


def draw_centered_text(
    surface: pygame.Surface,
    lines: list[str],
    *,
    y_start: int = 80,
    color: tuple[int, int, int] = colors.TEXT_BODY,
    size: int | None = None,
) -> None:
    pt = size if size is not None else HUD_BODY_PT + 4
    font = body_font(pt)
    sw = surface.get_width()
    y = y_start
    for line in lines:
        text = font.render(line, True, color)
        x = (sw - text.get_width()) // 2
        clip = pygame.Rect(16, y, sw - 32, pt + 8)
        old_clip = surface.get_clip()
        surface.set_clip(clip)
        surface.blit(text, (x, y))
        surface.set_clip(old_clip)
        y += pt + 12
