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


def clear_icon_cache() -> None:
    _ICON_CACHE.clear()
