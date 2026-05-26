"""Heads-up display text for simulation and replay."""

from __future__ import annotations

from pathlib import Path

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
_HUD_MENTOR_GAP = 12
_MENTOR_PATH = Path(__file__).resolve().parents[1] / "assets" / "icons" / "mentor_1.png"
_MENTOR_CACHE: dict[int, pygame.Surface | None] = {}


def _mentor_surface(max_height: int) -> pygame.Surface | None:
    if max_height in _MENTOR_CACHE:
        return _MENTOR_CACHE[max_height]
    if not _MENTOR_PATH.is_file():
        _MENTOR_CACHE[max_height] = None
        return None
    try:
        image = pygame.image.load(str(_MENTOR_PATH))
        if pygame.display.get_surface() is not None:
            image = image.convert_alpha()
        src_w, src_h = image.get_size()
        if src_h <= 0:
            _MENTOR_CACHE[max_height] = None
            return None
        display_h = min(max_height, src_h)
        display_w = max(1, int(display_h * src_w / src_h))
        scaled = pygame.transform.smoothscale(image, (display_w, display_h))
        _MENTOR_CACHE[max_height] = scaled
        return scaled
    except pygame.error:
        _MENTOR_CACHE[max_height] = None
        return None


def _wrap_text(text: str, font: pygame.font.Font, max_w: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip() if current else word
        if font.size(trial)[0] <= max_w:
            current = trial
            continue
        if current:
            lines.append(current)
            current = word
            continue
        current = word
    if current:
        lines.append(current)
    return lines or [text]


def _hud_text_column(panel: pygame.Rect) -> tuple[int, int, pygame.Surface | None]:
    inner_h = max(1, panel.height - _HUD_PAD_Y * 2)
    mentor = _mentor_surface(inner_h)
    if mentor is None:
        return _HUD_PAD_X, panel.width - _HUD_PAD_X * 2, None
    text_x = _HUD_PAD_X + mentor.get_width() + _HUD_MENTOR_GAP
    text_w = max(80, panel.width - text_x - _HUD_PAD_X)
    return text_x, text_w, mentor


def _draw_wrapped_entry(
    surface: pygame.Surface,
    *,
    text: str,
    rect_x: int,
    rect_w: int,
    y: int,
    line_h: int,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    panel_bottom: int,
) -> int:
    for line in _wrap_text(text, font, rect_w):
        if y + line_h > panel_bottom - _HUD_PAD_Y:
            return y
        skin.draw_text_clipped(
            surface,
            line,
            pygame.Rect(rect_x, y, rect_w, line_h),
            font,
            color,
            align="left",
        )
        y += line_h
    return y


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
    subtitle_font = body_font(max(HUD_BODY_PT - 2, 13))
    text_x, text_w, mentor = _hud_text_column(panel)

    old_clip = surface.get_clip()
    surface.set_clip(panel)

    if mentor is not None:
        inner_h = panel.height - _HUD_PAD_Y * 2
        mentor_y = panel_top + _HUD_PAD_Y + (inner_h - mentor.get_height()) // 2
        surface.blit(mentor, (_HUD_PAD_X, mentor_y))

    y = panel_top + _HUD_PAD_Y
    panel_bottom = panel.bottom

    y = _draw_wrapped_entry(
        surface,
        text=title,
        rect_x=text_x,
        rect_w=text_w,
        y=y,
        line_h=HUD_TITLE_PT + 4,
        font=title_font_obj,
        color=colors.GOLD_TEXT,
        panel_bottom=panel_bottom,
    )
    y += _HUD_TITLE_GAP

    if subtitle:
        y = _draw_wrapped_entry(
            surface,
            text=subtitle,
            rect_x=text_x,
            rect_w=text_w,
            y=y,
            line_h=HUD_BODY_PT,
            font=subtitle_font,
            color=colors.TEXT_MUTED,
            panel_bottom=panel_bottom,
        )
        y += _HUD_SUBTITLE_GAP

    for line in lines[:4]:
        if not line:
            continue
        y = _draw_wrapped_entry(
            surface,
            text=line,
            rect_x=text_x,
            rect_w=text_w,
            y=y,
            line_h=_HUD_BODY_LINE,
            font=body_font_obj,
            color=colors.TEXT_BODY,
            panel_bottom=panel_bottom,
        )

    if footer:
        skin.draw_text_clipped(
            surface,
            footer,
            pygame.Rect(
                text_x,
                panel.bottom - _HUD_PAD_Y - HUD_BODY_PT,
                text_w,
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
