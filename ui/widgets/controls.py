"""Hit-tested widgets for Pygame screens."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pygame

from ui.theme import (
    COLOR_ACCENT,
    COLOR_MUTED,
    COLOR_PANEL,
    COLOR_TEXT,
    MIN_HIT_SIZE,
)


class Widget:
    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect
        self.enabled = True
        self.hovered = False
        self._pressed = False
        self.hint = ""

    def contains(self, pos: tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)

    def handle_event(self, event: pygame.event.Event) -> bool:
        return False

    def draw(self, surface: pygame.Surface) -> None:
        raise NotImplementedError


class WidgetGroup:
    def __init__(self, widgets: list[Widget] | None = None) -> None:
        self.widgets = widgets or []
        self.focused: Widget | None = None

    def add(self, widget: Widget) -> None:
        self.widgets.append(widget)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            over_any = False
            for widget in self.widgets:
                widget.hovered = widget.enabled and widget.contains(pos)
                over_any = over_any or widget.hovered
            if over_any:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for widget in reversed(self.widgets):
                if not widget.enabled or not widget.contains(event.pos):
                    continue
                if widget.handle_event(event):
                    if isinstance(widget, TextField):
                        self.focused = widget
                    return True
            self.focused = None
            return False

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for widget in reversed(self.widgets):
                if widget.handle_event(event):
                    return True

        if event.type == pygame.KEYDOWN and self.focused is not None:
            if self.focused.handle_event(event):
                return True

        return False

    def draw(self, surface: pygame.Surface) -> None:
        for widget in self.widgets:
            widget.draw(surface)


def _ensure_min_size(rect: pygame.Rect) -> pygame.Rect:
    w = max(rect.width, MIN_HIT_SIZE)
    h = max(rect.height, MIN_HIT_SIZE)
    if w == rect.width and h == rect.height:
        return rect
    out = rect.copy()
    out.w = w
    out.h = h
    return out


class Button(Widget):
    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        *,
        on_click: Callable[[], None] | None = None,
        font_size: int = 18,
    ) -> None:
        super().__init__(_ensure_min_size(rect))
        self.label = label
        self.on_click = on_click
        self._font_size = font_size

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.contains(event.pos):
                self._pressed = True
                return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pressed and self.contains(event.pos) and self.on_click:
                self.on_click()
            self._pressed = False
            return self._pressed or self.contains(event.pos)
        return False

    def draw(self, surface: pygame.Surface) -> None:
        font = pygame.font.SysFont("consolas,courier,monospace", self._font_size)
        if not self.enabled:
            fill = (50, 54, 62)
            text_color = COLOR_MUTED
        elif self._pressed:
            fill = (60, 120, 180)
            text_color = COLOR_TEXT
        elif self.hovered:
            fill = COLOR_ACCENT
            text_color = (16, 20, 28)
        else:
            fill = COLOR_PANEL
            text_color = COLOR_TEXT
        pygame.draw.rect(surface, fill, self.rect, border_radius=4)
        pygame.draw.rect(surface, (60, 68, 82), self.rect, 1, border_radius=4)
        text = font.render(self.label, True, text_color)
        tx = self.rect.x + (self.rect.width - text.get_width()) // 2
        ty = self.rect.y + (self.rect.height - text.get_height()) // 2
        surface.blit(text, (tx, ty))


class ListRow(Widget):
    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        *,
        selected: bool = False,
        on_click: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(_ensure_min_size(rect))
        self.label = label
        self.selected = selected
        self.on_click = on_click

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.contains(event.pos):
            if self.on_click:
                self.on_click()
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        font = pygame.font.SysFont("consolas,courier,monospace", 18)
        if self.selected:
            pygame.draw.rect(surface, (40, 56, 72), self.rect, border_radius=3)
        color = COLOR_ACCENT if self.selected else (COLOR_TEXT if self.enabled else COLOR_MUTED)
        prefix = "> " if self.selected else "  "
        text = font.render(f"{prefix}{self.label}", True, color)
        surface.blit(text, (self.rect.x + 6, self.rect.y + 6))


class Stepper(Widget):
    def __init__(
        self,
        rect: pygame.Rect,
        *,
        value: int,
        on_change: Callable[[int], None],
        min_value: int = 0,
        max_value: int = 999_999,
    ) -> None:
        super().__init__(rect)
        self._value = value
        self.on_change = on_change
        self.min_value = min_value
        self.max_value = max_value
        w = rect.width // 3
        self._minus = Button(pygame.Rect(rect.x, rect.y, w, rect.height), "-", on_click=self._dec)
        self._plus = Button(
            pygame.Rect(rect.x + 2 * w, rect.y, w, rect.height),
            "+",
            on_click=self._inc,
        )
        self._label_rect = pygame.Rect(rect.x + w, rect.y, w, rect.height)

    def _dec(self) -> None:
        self.on_change(max(self.min_value, self._value - 1))

    def _inc(self) -> None:
        self.on_change(min(self.max_value, self._value + 1))

    def set_value(self, value: int) -> None:
        self._value = value

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False
        return self._minus.handle_event(event) or self._plus.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        self._minus.enabled = self.enabled
        self._plus.enabled = self.enabled
        self._minus.draw(surface)
        self._plus.draw(surface)
        font = pygame.font.SysFont("consolas,courier,monospace", 18)
        text = font.render(str(self._value), True, COLOR_TEXT if self.enabled else COLOR_MUTED)
        tx = self._label_rect.x + (self._label_rect.width - text.get_width()) // 2
        ty = self._label_rect.y + (self._label_rect.height - text.get_height()) // 2
        surface.blit(text, (tx, ty))
        if self.hovered and not self.enabled and self.hint:
            hint_font = pygame.font.SysFont("consolas,courier,monospace", 14)
            hint = hint_font.render(self.hint, True, COLOR_MUTED)
            surface.blit(hint, (self.rect.x, self.rect.bottom + 4))


class TextField(Widget):
    def __init__(
        self,
        rect: pygame.Rect,
        *,
        text: str,
        on_change: Callable[[str], None],
        max_length: int = 80,
    ) -> None:
        super().__init__(_ensure_min_size(rect))
        self.text = text
        self.on_change = on_change
        self.max_length = max_length
        self.focused = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.focused = self.contains(event.pos)
            return self.focused
        if not self.focused:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.focused = False
                return True
            if event.key == pygame.K_ESCAPE:
                self.focused = False
                return True
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                self.on_change(self.text)
                return True
            if event.unicode and event.unicode.isprintable() and len(self.text) < self.max_length:
                self.text += event.unicode
                self.on_change(self.text)
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        border = COLOR_ACCENT if self.focused else (100, 110, 130)
        pygame.draw.rect(surface, (32, 36, 46), self.rect, border_radius=3)
        pygame.draw.rect(surface, border, self.rect, 2, border_radius=3)
        font = pygame.font.SysFont("consolas,courier,monospace", 16)
        shown = self.text + ("|" if self.focused else "")
        label = font.render(shown, True, COLOR_TEXT)
        surface.blit(label, (self.rect.x + 8, self.rect.y + 8))
