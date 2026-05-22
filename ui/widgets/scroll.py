"""Simple vertical scroll state for coach panels."""

from __future__ import annotations

import pygame


class ScrollState:
    def __init__(self, *, content_height: int = 0, viewport_height: int = 0) -> None:
        self.content_height = content_height
        self.viewport_height = viewport_height
        self.offset = 0

    @property
    def max_offset(self) -> int:
        return max(0, self.content_height - self.viewport_height)

    def set_content(self, content_height: int, viewport_height: int) -> None:
        self.content_height = content_height
        self.viewport_height = viewport_height
        self.offset = min(self.offset, self.max_offset)

    def scroll(self, delta: int) -> None:
        self.offset = max(0, min(self.max_offset, self.offset + delta))

    def handle_wheel(self, event: pygame.event.Event, *, rect: pygame.Rect) -> bool:
        if event.type != pygame.MOUSEWHEEL:
            return False
        if not rect.collidepoint(pygame.mouse.get_pos()):
            return False
        self.scroll(-event.y * 24)
        return True
