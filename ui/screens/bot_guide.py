"""Bot-writing guide for the selected scenario."""

from __future__ import annotations

import pygame

from engine.core.scenario_registry import scenario_display_name
from ui.bot_guide_content import guide_blocks_for_scenario
from ui.bot_guide_layout import draw_guide_content, draw_guide_scrollbar, measure_guide_content
from ui.skin import chrome as skin
from ui.theme import MARGIN_X, WINDOW_HEIGHT, content_width
from ui.widgets import Button, WidgetGroup
from ui.widgets.scroll import ScrollState

_CONTENT_TOP = 88
_FOOTER_H = 52
_SCROLLBAR_W = 8
_INSET = 20


class BotGuideScreen:
    def __init__(self, app: object) -> None:
        self.app = app
        self.scenario_id = "resource_wars"
        self._scroll = ScrollState()
        self._blocks: list = []
        self._back_btn = Button(
            pygame.Rect(MARGIN_X, 0, 140, 40),
            "Back to Menu",
            on_click=lambda: self.app.goto_menu(),
        )
        self._widgets = WidgetGroup([self._back_btn])

    def open_scenario(self, scenario_id: str) -> None:
        self.scenario_id = scenario_id
        self._blocks = guide_blocks_for_scenario(scenario_id)
        self._scroll.offset = 0

    def on_enter(self) -> None:
        self._scroll.offset = 0

    def _content_rect(self, *, window_height: int | None = None) -> pygame.Rect:
        sh = window_height if window_height is not None else WINDOW_HEIGHT
        top = _CONTENT_TOP
        bottom = sh - _FOOTER_H - 12
        return pygame.Rect(
            MARGIN_X + _INSET,
            top,
            content_width() - 2 * _INSET - _SCROLLBAR_W - 4,
            max(100, bottom - top),
        )

    def _update_scroll_metrics(self, *, window_height: int) -> None:
        rect = self._content_rect(window_height=window_height)
        total = measure_guide_content(self._blocks, content_width=rect.width)
        self._scroll.set_content(total, rect.height)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._widgets.handle_event(event):
            return
        rect = self._content_rect()
        if self._scroll.handle_wheel(event, rect=rect):
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.goto_menu()

    def draw(self, surface: pygame.Surface) -> None:
        skin.draw_background(surface)
        sw, sh = surface.get_width(), surface.get_height()
        name = scenario_display_name(self.scenario_id)
        title = f"How to write a bot for {name}"

        skin.draw_banner_title(
            surface,
            title,
            center_x=sw // 2,
            y=18,
            max_width=content_width(),
        )

        content = self._content_rect(window_height=sh)
        self._update_scroll_metrics(window_height=sh)

        panel = pygame.Rect(
            MARGIN_X,
            content.y - 8,
            content_width(),
            content.height + 16,
        )
        skin.draw_panel(surface, panel, style="stone")

        draw_guide_content(
            surface,
            content,
            self._blocks,
            self._scroll.offset,
        )

        track = pygame.Rect(
            panel.right - _SCROLLBAR_W - 10,
            content.y,
            _SCROLLBAR_W,
            content.height,
        )
        draw_guide_scrollbar(
            surface,
            track,
            content_height=self._scroll.content_height,
            viewport_height=self._scroll.viewport_height,
            offset=self._scroll.offset,
        )

        self._back_btn.rect = pygame.Rect(
            MARGIN_X,
            sh - _FOOTER_H,
            160,
            40,
        )
        self._widgets.draw(surface)
