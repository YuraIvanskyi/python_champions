"""Radio and language pickers for the settings screen."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from ui.audio import play_ui_click
from ui.render.icons import draw_menu_icon
from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font
from ui.widgets.controls import Widget, _ensure_min_size

_RADIO_R = 7
_RADIO_GAP = 10


class RadioPicker(Widget):
    """Vertical radio-button list — one option selected at a time."""

    def __init__(
        self,
        rect: pygame.Rect,
        *,
        options: list[tuple[str, str]],
        value: str,
        on_change: Callable[[str], None],
        row_height: int = 28,
    ) -> None:
        super().__init__(_ensure_min_size(rect))
        self.options = options
        self._selected = value if any(v == value for v, _ in options) else options[0][0]
        self.on_change = on_change
        self.row_height = row_height
        self._pressed_value: str | None = None

    @property
    def value(self) -> str:
        return self._selected

    def set_value(self, value: str) -> None:
        if any(v == value for v, _ in self.options):
            self._selected = value

    def _row_rect(self, index: int) -> pygame.Rect:
        return pygame.Rect(
            self.rect.x,
            self.rect.y + index * self.row_height,
            self.rect.width,
            self.row_height,
        )

    def _radio_center(self, row: pygame.Rect) -> tuple[int, int]:
        return row.x + _RADIO_R + 4, row.centery

    def _hit_value(self, pos: tuple[int, int]) -> str | None:
        for i, (val, _label) in enumerate(self.options):
            if self._row_rect(i).collidepoint(pos):
                return val
        return None

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            hit = self._hit_value(event.pos)
            if hit is not None:
                self._pressed_value = hit
                return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            hit = self._hit_value(event.pos)
            if self._pressed_value is not None and hit == self._pressed_value:
                self._selected = hit
                play_ui_click()
                self.on_change(self._selected)
            self._pressed_value = None
            return hit is not None
        return False

    def draw(self, surface: pygame.Surface) -> None:
        font = body_font(14)
        for i, (val, label) in enumerate(self.options):
            row = self._row_rect(i)
            selected = val == self._selected
            cx, cy = self._radio_center(row)

            outer = pygame.Rect(cx - _RADIO_R, cy - _RADIO_R, _RADIO_R * 2, _RADIO_R * 2)
            pygame.draw.circle(surface, colors.WOOD_BORDER, outer.center, _RADIO_R + 1)
            pygame.draw.circle(surface, colors.SLATE_PANEL, outer.center, _RADIO_R)
            if selected:
                pygame.draw.circle(surface, colors.TEAL_ACCENT, outer.center, _RADIO_R - 3)

            text_x = cx + _RADIO_R + _RADIO_GAP
            text_color = colors.GOLD_TEXT if selected else colors.TEXT_BODY
            skin.draw_text_clipped(
                surface,
                label,
                pygame.Rect(text_x, row.y, row.width - (text_x - row.x), row.height),
                font,
                text_color,
                align="left",
                pad_y=4,
            )


class LanguagePicker(Widget):
    """Two side-by-side language cards with flag icons."""

    def __init__(
        self,
        rect: pygame.Rect,
        *,
        options: list[tuple[str, str, str]],
        value: str,
        on_change: Callable[[str], None],
    ) -> None:
        super().__init__(_ensure_min_size(rect))
        self.options = options
        self._selected = value if any(v == value for v, _, _ in options) else options[0][0]
        self.on_change = on_change
        self._pressed: str | None = None

    @property
    def value(self) -> str:
        return self._selected

    def set_value(self, value: str) -> None:
        if any(v == value for v, _, _ in self.options):
            self._selected = value

    def _card_rect(self, index: int) -> pygame.Rect:
        gap = 8
        card_w = (self.rect.width - gap) // 2
        return pygame.Rect(
            self.rect.x + index * (card_w + gap),
            self.rect.y,
            card_w,
            self.rect.height,
        )

    def _hit_value(self, pos: tuple[int, int]) -> str | None:
        for i, (val, _, _icon) in enumerate(self.options):
            if self._card_rect(i).collidepoint(pos):
                return val
        return None

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            hit = self._hit_value(event.pos)
            if hit is not None:
                self._pressed = hit
                return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            hit = self._hit_value(event.pos)
            if self._pressed is not None and hit == self._pressed:
                self._selected = hit
                play_ui_click()
                self.on_change(self._selected)
            self._pressed = None
            return hit is not None
        return False

    def draw(self, surface: pygame.Surface) -> None:
        font = body_font(14)
        for i, (val, label, icon_name) in enumerate(self.options):
            card = self._card_rect(i)
            selected = val == self._selected
            style = "parchment" if selected else "wood"
            skin.draw_panel(surface, card, style=style)
            if selected:
                pygame.draw.rect(surface, colors.TEAL_ACCENT, card, 2, border_radius=6)

            icon_size = min(28, card.height - 12)
            icon_rect = pygame.Rect(card.x + 10, card.centery - icon_size // 2, icon_size, icon_size)
            draw_menu_icon(surface, icon_name, icon_rect, colors.GOLD_TEXT)

            text_rect = pygame.Rect(
                icon_rect.right + 8,
                card.y,
                card.width - icon_rect.width - 26,
                card.height,
            )
            text_color = colors.PARCHMENT_TEXT if selected else colors.TEXT_BODY
            skin.draw_text_clipped(
                surface,
                label,
                text_rect,
                font,
                text_color,
                align="left",
                pad_y=8,
            )
