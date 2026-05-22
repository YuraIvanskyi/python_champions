"""Cached entity icon surfaces."""

from __future__ import annotations

from pathlib import Path

import pygame

_ICON_CACHE: dict[str, pygame.Surface | None] = {}


def load_icon(path: str | None, *, size: int = 24) -> pygame.Surface | None:
    if not path:
        return None
    key = f"{path}:{size}"
    if key in _ICON_CACHE:
        return _ICON_CACHE[key]

    file_path = Path(path)
    if not file_path.is_file():
        _ICON_CACHE[key] = None
        return None

    try:
        image = pygame.image.load(str(file_path)).convert_alpha()
        image = pygame.transform.smoothscale(image, (size, size))
        _ICON_CACHE[key] = image
        return image
    except pygame.error:
        _ICON_CACHE[key] = None
        return None


def draw_portrait_frame(
    surface: pygame.Surface,
    center: tuple[int, int],
    *,
    size: int = 32,
    color: tuple[int, int, int] = (100, 72, 48),
) -> None:
    """Decorative portrait border tinted to the entity's color."""
    half = size // 2 + 3
    rect = pygame.Rect(center[0] - half, center[1] - half, half * 2, half * 2)

    # Semi-transparent tinted backdrop
    r, g, b = color
    bg = pygame.Surface(rect.size, pygame.SRCALPHA)
    bg.fill((max(0, r - 55), max(0, g - 55), max(0, b - 55), 150))
    surface.blit(bg, rect.topleft)

    # Outer border in entity color
    pygame.draw.rect(surface, color, rect, 2, border_radius=4)
    # Thin inner highlight ring
    inner = rect.inflate(-4, -4)
    if inner.width > 4:
        lighter = (min(255, r + 60), min(255, g + 60), min(255, b + 60))
        pygame.draw.rect(surface, lighter, inner, 1, border_radius=3)
    # Dark outer halo for contrast against any tile colour
    pygame.draw.rect(surface, (16, 20, 28), rect.inflate(2, 2), 1, border_radius=5)


def clear_icon_cache() -> None:
    _ICON_CACHE.clear()
