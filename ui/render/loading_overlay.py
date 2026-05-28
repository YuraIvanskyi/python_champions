"""Full-screen RPG loading overlay with animated spinner."""

from __future__ import annotations

import math

import pygame

from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font
from ui.skin.typography import title_font as title_font_fn

def draw_loading_overlay(
    surface: pygame.Surface,
    *,
    message: str | None = None,
    subtitle: str | None = None,
    spinner_angle: float = 0.0,
    lang: str = "en",
) -> None:
    """Dim the screen and draw a centered stone panel with a rotating rune ring."""
    from engine.i18n import translate

    if message is None:
        message = translate("loading.preparing", lang=lang)
    if subtitle is None:
        subtitle = translate("loading.analyzing", lang=lang)
    w, h = surface.get_size()

    dim = pygame.Surface((w, h), pygame.SRCALPHA)
    dim.fill((8, 10, 18, 170))
    surface.blit(dim, (0, 0))

    pw = min(400, w - 40)
    ph = 176
    panel = pygame.Rect((w - pw) // 2, (h - ph) // 2, pw, ph)
    skin.draw_panel(surface, panel, style="stone")

    cx = panel.centerx
    cy = panel.y + 58
    _draw_rune_spinner(surface, cx, cy, spinner_angle)

    title_y = panel.y + 98
    font = title_font_fn(20)
    title_surf = font.render(message, True, colors.GOLD_TEXT)
    surface.blit(title_surf, (cx - title_surf.get_width() // 2, title_y))

    sub_font = body_font(14)
    sub_surf = sub_font.render(subtitle, True, colors.TEXT_MUTED)
    surface.blit(sub_surf, (cx - sub_surf.get_width() // 2, title_y + title_surf.get_height() + 6))


def _draw_rune_spinner(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    angle: float,
    *,
    orbit_radius: int = 30,
    mark_count: int = 8,
) -> None:
    """Rotating ring of gold diamond runes with a pulsing center gem."""
    for i in range(mark_count):
        theta = angle + (2.0 * math.pi * i / mark_count)
        phase = (angle * 1.8 + i * 0.55) % (2.0 * math.pi)
        alpha = int(70 + 185 * (0.5 + 0.5 * math.sin(phase)))
        mx = cx + int(math.cos(theta) * orbit_radius)
        my = cy + int(math.sin(theta) * orbit_radius)
        _draw_rune_mark(surface, mx, my, alpha)

    pulse = 0.5 + 0.5 * math.sin(angle * 2.4)
    core_r = int(5 + pulse * 2)
    pygame.draw.circle(surface, colors.STONE_SHADOW, (cx, cy), core_r + 3)
    pygame.draw.circle(surface, colors.GOLD_TEXT, (cx, cy), core_r)
    highlight = (
        min(255, colors.GOLD_TEXT[0] + 40),
        min(255, colors.GOLD_TEXT[1] + 40),
        min(255, colors.GOLD_TEXT[2]),
    )
    pygame.draw.circle(surface, highlight, (cx - 1, cy - 1), max(2, core_r - 2))

    ring_r = orbit_radius - 6
    arc_span = math.pi * 0.55
    start_deg = math.degrees(angle)
    rect = pygame.Rect(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2)
    pygame.draw.arc(surface, colors.TEAL_ACCENT, rect, start_deg, start_deg + math.degrees(arc_span), 2)
    pygame.draw.arc(
        surface,
        colors.STONE_HIGHLIGHT,
        rect,
        start_deg + math.degrees(math.pi),
        start_deg + math.degrees(math.pi + arc_span),
        2,
    )


def _draw_rune_mark(surface: pygame.Surface, x: int, y: int, alpha: int) -> None:
    """Small diamond rune with alpha."""
    d = 5
    pts = [(x, y - d), (x + d, y), (x, y + d), (x - d, y)]
    mark = pygame.Surface((d * 2 + 2, d * 2 + 2), pygame.SRCALPHA)
    local = [(p[0] - x + d, p[1] - y + d) for p in pts]
    pygame.draw.polygon(mark, (*colors.GOLD_TEXT, alpha), local)
    pygame.draw.polygon(mark, (*colors.STONE_SHADOW, min(255, alpha)), local, 1)
    surface.blit(mark, (x - d, y - d))
