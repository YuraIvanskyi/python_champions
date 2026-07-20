"""Shared layout invalidation for Pygame screens."""

from __future__ import annotations

import pygame


class LayoutMixin:
    _layout_size: tuple[int, int] | None = None

    def ensure_layout(self, surface: pygame.Surface) -> None:
        size = surface.get_size()
        if self._layout_size != size:
            self._layout(surface)
            self._layout_size = size

    def _layout(self, surface: pygame.Surface) -> None:
        raise NotImplementedError

    def invalidate_layout(self) -> None:
        self._layout_size = None
