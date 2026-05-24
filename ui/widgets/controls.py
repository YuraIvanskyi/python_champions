"""Hit-tested widgets for Pygame screens."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from ui.render.icons import draw_menu_icon
from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font, code_font
from ui.theme import MIN_HIT_SIZE

# ── Per-widget padding constants ──────────────────────────────────────────────
BUTTON_PAD_X = 12
BUTTON_PAD_Y = 6
ROW_PAD_X = 14
ROW_PAD_Y = 6
FIELD_PAD_X = 8
FIELD_PAD_Y = 4


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
        primary: bool = False,
        icon: str | None = None,
        icon_size: int = 16,
    ) -> None:
        super().__init__(_ensure_min_size(rect))
        self.label = label
        self.on_click = on_click
        self._font_size = font_size
        self.primary = primary
        self.icon = icon
        self._icon_size = icon_size

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
        if self.primary:
            skin.draw_primary_button(
                surface,
                self.rect,
                self.label,
                hovered=self.hovered and self.enabled,
                pressed=self._pressed,
                enabled=self.enabled,
            )
            return

        skin.draw_panel(surface, self.rect, style="stone")

        # State overlays — hover brightens, pressed darkens
        if self.enabled:
            if self._pressed:
                overlay = pygame.Surface(self.rect.size, pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 70))
                surface.blit(overlay, self.rect.topleft)
            elif self.hovered:
                overlay = pygame.Surface(self.rect.size, pygame.SRCALPHA)
                overlay.fill((100, 130, 170, 38))
                surface.blit(overlay, self.rect.topleft)
                pygame.draw.rect(surface, colors.STONE_HIGHLIGHT,
                                 self.rect, 1, border_radius=6)

        font = body_font(self._font_size)
        if not self.enabled:
            text_color = (78, 86, 104)
        elif self._pressed:
            text_color = colors.TEXT_BODY
        elif self.hovered:
            text_color = colors.TEXT_BODY
        else:
            text_color = colors.GOLD_TEXT

        shift_y = 1 if self._pressed else 0
        text_surf = font.render(self.label, True, text_color)

        has_text = bool(self.label)
        icon_gap = 6 if (self.icon and has_text) else 0
        icon_total = self._icon_size + icon_gap if self.icon else 0
        avail_w = self.rect.width - BUTTON_PAD_X * 2 - icon_total
        display = self.label
        while display and text_surf.get_width() > avail_w:
            display = display[:-1]
            text_surf = font.render(display + "…", True, text_color)

        content_w = text_surf.get_width() + icon_total
        content_x = self.rect.x + (self.rect.width - content_w) // 2
        text_y = self.rect.y + (self.rect.height - text_surf.get_height()) // 2 + shift_y

        old_clip = surface.get_clip()
        surface.set_clip(self.rect.inflate(-2, -2))

        if self.icon:
            icon_color = text_color if isinstance(text_color, tuple) else colors.GOLD_TEXT
            icon_rect = pygame.Rect(content_x, self.rect.y, self._icon_size, self.rect.height)
            draw_menu_icon(surface, self.icon, icon_rect, icon_color)
            surface.blit(text_surf, (content_x + icon_total, text_y))
        else:
            surface.blit(text_surf, (content_x, text_y))

        surface.set_clip(old_clip)


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
        style = "parchment" if self.selected else "wood"
        skin.draw_panel(surface, self.rect, style=style)

        # Hover tint for unselected rows
        if self.hovered and not self.selected and self.enabled:
            overlay = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            overlay.fill((255, 220, 120, 22))
            surface.blit(overlay, self.rect.topleft)

        if self.selected:
            bar = pygame.Rect(self.rect.x, self.rect.y, 4, self.rect.height)
            pygame.draw.rect(surface, colors.TEAL_ACCENT, bar, border_radius=2)
            pygame.draw.rect(surface, colors.TEAL_ACCENT, self.rect, 1, border_radius=6)

        font = body_font(16)
        if self.selected:
            color = colors.PARCHMENT_TEXT if style == "parchment" else colors.GOLD_TEXT
        elif self.hovered and self.enabled:
            color = colors.TEXT_BODY
        elif self.enabled:
            color = colors.TEXT_BODY
        else:
            color = colors.TEXT_MUTED

        prefix = "> " if self.selected else "  "
        skin.draw_text_clipped(
            surface,
            f"{prefix}{self.label}",
            pygame.Rect(self.rect.x + 8, self.rect.y, self.rect.width - 16, self.rect.height),
            font,
            color,
            align="left",
            pad_x=ROW_PAD_X - 8,
            pad_y=ROW_PAD_Y,
        )


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
        skin.draw_panel(surface, self.rect, style="stone")
        if self.focused:
            pygame.draw.rect(surface, colors.GOLD_TEXT, self.rect, 2, border_radius=4)

        font = code_font(15)
        shown = self.text + ("|" if self.focused else "")

        # Show the tail end of the text so the cursor is always visible
        inner_w = self.rect.width - FIELD_PAD_X * 2
        rendered = font.render(shown, True, colors.TEXT_BODY)
        if rendered.get_width() > inner_w and inner_w > 0:
            # Trim from the front until it fits
            trimmed = shown
            while len(trimmed) > 1:
                trimmed = trimmed[1:]
                rendered = font.render("…" + trimmed, True, colors.TEXT_BODY)
                if rendered.get_width() <= inner_w:
                    break

        inner = self.rect.inflate(-FIELD_PAD_X * 2, -FIELD_PAD_Y * 2)
        old_clip = surface.get_clip()
        surface.set_clip(inner)
        surface.blit(rendered, (inner.x, inner.y + (inner.height - rendered.get_height()) // 2))
        surface.set_clip(old_clip)
