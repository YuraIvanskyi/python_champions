"""Heads-up display text for simulation and replay."""

from __future__ import annotations

import pygame

from ui.theme import COLOR_ACCENT, COLOR_MUTED, COLOR_TEXT, HUD_TEXT_HEIGHT


def _font(size: int = 18) -> pygame.font.Font:
    return pygame.font.SysFont("consolas,courier,monospace", size)


def draw_hud(
    surface: pygame.Surface,
    *,
    title: str,
    lines: list[str],
    footer: str = "",
    y_offset: int | None = None,
    content_height: int = HUD_TEXT_HEIGHT,
) -> None:
    panel_top = y_offset if y_offset is not None else surface.get_height() - content_height
    panel = pygame.Rect(0, panel_top, surface.get_width(), content_height)
    pygame.draw.rect(surface, (32, 38, 48), panel)
    pygame.draw.line(surface, (60, 68, 82), (0, panel_top), (surface.get_width(), panel_top), 1)

    title_font = _font(20)
    body_font = _font(16)
    y = panel_top + 10
    title_surf = title_font.render(title, True, COLOR_ACCENT)
    surface.blit(title_surf, (16, y))
    y += 30

    for line in lines[:4]:
        text = body_font.render(line, True, COLOR_TEXT)
        surface.blit(text, (16, y))
        y += 22

    if footer:
        foot = body_font.render(footer, True, COLOR_MUTED)
        surface.blit(foot, (16, panel.bottom - 24))


def draw_toolbar_strip(surface: pygame.Surface, *, y: int, height: int) -> None:
    """Background band for control buttons below HUD text."""
    strip = pygame.Rect(0, y, surface.get_width(), height)
    pygame.draw.rect(surface, (28, 32, 40), strip)
    pygame.draw.line(surface, (60, 68, 82), (0, y), (surface.get_width(), y), 1)


def draw_centered_text(
    surface: pygame.Surface,
    lines: list[str],
    *,
    y_start: int = 80,
    color: tuple[int, int, int] = COLOR_TEXT,
    size: int = 22,
) -> None:
    font = _font(size)
    y = y_start
    for line in lines:
        text = font.render(line, True, color)
        rect = text.get_rect(center=(surface.get_width() // 2, y))
        surface.blit(text, rect)
        y += size + 12
