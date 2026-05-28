"""Global game settings — language, AI model, scenario map params."""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from engine.core.config import AppConfig
from engine.core.config_io import (
    SCENARIO_SETTINGS_FIELDS,
    SettingsValidationError,
    reload_app_config,
    save_app_config,
    save_scenario_settings,
    validate_scenario_field,
)
from engine.core.scenario_config import load_scenario_section
from engine.core.scenario_registry import list_scenarios, scenario_display_name
from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font
from ui.theme import MARGIN_X, WINDOW_HEIGHT, content_width
from ui.widgets import Button, LanguagePicker, RadioPicker, TextField, Widget, WidgetGroup
from ui.widgets.scroll import ScrollState

_CONTENT_TOP = 88
_FOOTER_H = 52
_SCROLLBAR_W = 8
_INSET = 16
_ROW_H = 30
_ROW_GAP = 4
_SECTION_GAP = 14
_SCENARIO_HEADER_H = 18
_SCENARIOS_TITLE_H = 24
_FIELD_INPUT_W = 52
_FIELD_COL_GAP = 12
_SCENARIO_COLS = 2
_SECTION_TITLE_H = 20
_LANG_CARD_H = 44
_MODEL_ROW_H = 28

LANGUAGE_OPTIONS: list[tuple[str, str, str]] = [
    ("en", "English", "flag_en"),
    ("uk", "Ukrainian", "flag_uk"),
]

AI_MODEL_OPTIONS: list[tuple[str, str]] = [
    ("qwen2.5:1.5b", "Qwen 2.5 1.5B (default)"),
    ("llama3.2:1b", "Llama 3.2 1B"),
    ("phi3:mini", "Phi-3 Mini"),
    ("gemma2:2b", "Gemma 2 2B"),
    ("smollm2:1.7b", "SmolLM2 1.7B"),
]

_FIELD_LABELS: dict[str, str] = {
    "map_width": "Width",
    "map_height": "Height",
    "obstacle_count": "Obstacles",
    "resource_count": "Resources",
    "pool_count": "Pools",
    "max_turns": "Max turns",
}


def _field_rows(keys: list[str]) -> list[list[str]]:
    """Pair scenario fields onto rows (two per row)."""
    rows: list[list[str]] = []
    for i in range(0, len(keys), _SCENARIO_COLS):
        rows.append(keys[i : i + _SCENARIO_COLS])
    return rows


@dataclass
class _ScenarioFields:
    scenario_id: str
    inputs: dict[str, TextField] = field(default_factory=dict)
    rows: list[list[str]] = field(default_factory=list)


class SettingsScreen:
    def __init__(self, app: object) -> None:
        self.app = app
        self._scroll = ScrollState()
        self._content_widgets: list[Widget] = []
        self._language: LanguagePicker | None = None
        self._ai_model: RadioPicker | None = None
        self._scenario_fields: list[_ScenarioFields] = []
        self._error_message = ""
        self._saved_until_ms = 0
        self._content_height = 0
        self._lang_title_y = 0
        self._model_title_y = 0
        self._scenarios_title_y = 0
        self._block_title_y: dict[str, int] = {}

        self._back_btn = Button(
            pygame.Rect(MARGIN_X, 0, 160, 40),
            "Back to Menu",
            on_click=lambda: self.app.goto_menu(),
        )
        self._save_btn = Button(
            pygame.Rect(0, 0, 140, 40),
            "Save",
            primary=True,
            on_click=self._save,
        )
        self._footer = WidgetGroup([self._back_btn, self._save_btn])

    def on_enter(self) -> None:
        self._scroll.offset = 0
        self._error_message = ""
        self._saved_until_ms = 0
        self._back_btn.label = self.app.t("settings.back")
        self._save_btn.label = self.app.t("settings.save")
        self._load_from_config(self.app.config)

    def _load_from_config(self, cfg: AppConfig) -> None:
        self._content_widgets.clear()
        self._scenario_fields.clear()
        self._block_title_y.clear()

        content_w = content_width() - 2 * _INSET - _SCROLLBAR_W - 4

        self._language = LanguagePicker(
            pygame.Rect(0, 0, content_w, _LANG_CARD_H),
            options=LANGUAGE_OPTIONS,
            value=cfg.locale.language,
            on_change=lambda _v: None,
        )
        model_h = len(AI_MODEL_OPTIONS) * _MODEL_ROW_H
        self._ai_model = RadioPicker(
            pygame.Rect(0, 0, content_w, model_h),
            options=AI_MODEL_OPTIONS,
            value=cfg.ai.model,
            on_change=lambda _v: None,
            row_height=_MODEL_ROW_H,
        )
        self._content_widgets.extend([self._language, self._ai_model])

        for entry in list_scenarios():
            sid = entry["id"]
            if sid not in SCENARIO_SETTINGS_FIELDS:
                continue
            section = load_scenario_section(sid)
            keys = SCENARIO_SETTINGS_FIELDS[sid]
            fields = _ScenarioFields(scenario_id=sid, rows=_field_rows(keys))
            for key in keys:
                raw = str(section.get(key, ""))
                fields.inputs[key] = TextField(
                    pygame.Rect(0, 0, _FIELD_INPUT_W, _ROW_H),
                    text=raw,
                    on_change=lambda _t: None,
                    max_length=4,
                    digits_only=True,
                )
                self._content_widgets.append(fields.inputs[key])
            self._scenario_fields.append(fields)

        self._recompute_layout()

    def _recompute_layout(self) -> None:
        y = 0
        self._lang_title_y = y
        y += _SECTION_TITLE_H + _LANG_CARD_H + _SECTION_GAP

        self._model_title_y = y
        y += _SECTION_TITLE_H + len(AI_MODEL_OPTIONS) * _MODEL_ROW_H + _SECTION_GAP

        self._scenarios_title_y = y
        y += _SCENARIOS_TITLE_H

        for block in self._scenario_fields:
            self._block_title_y[block.scenario_id] = y
            y += _SCENARIO_HEADER_H
            y += len(block.rows) * (_ROW_H + _ROW_GAP)
            y += _SECTION_GAP

        self._content_height = y + 12

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

    def _cell_width(self, content: pygame.Rect) -> int:
        return (content.width - _FIELD_COL_GAP) // _SCENARIO_COLS

    def _layout_scenario_field(
        self,
        content: pygame.Rect,
        *,
        y: int,
        col: int,
        input_field: TextField,
    ) -> None:
        cell_w = self._cell_width(content)
        cell_x = content.x + col * (cell_w + _FIELD_COL_GAP)
        input_field.rect = pygame.Rect(
            cell_x + cell_w - _FIELD_INPUT_W,
            y,
            _FIELD_INPUT_W,
            _ROW_H,
        )

    def _apply_scroll_layout(self, content: pygame.Rect) -> None:
        y = content.y - self._scroll.offset

        y += _SECTION_TITLE_H
        if self._language is not None:
            self._language.rect = pygame.Rect(content.x, y, content.width, _LANG_CARD_H)
            y += _LANG_CARD_H + _SECTION_GAP

        y += _SECTION_TITLE_H
        if self._ai_model is not None:
            model_h = len(AI_MODEL_OPTIONS) * _MODEL_ROW_H
            self._ai_model.rect = pygame.Rect(content.x, y, content.width, model_h)
            y += model_h + _SECTION_GAP

        y += _SCENARIOS_TITLE_H

        for block in self._scenario_fields:
            y += _SCENARIO_HEADER_H
            for row_keys in block.rows:
                for col, key in enumerate(row_keys):
                    self._layout_scenario_field(
                        content,
                        y=y,
                        col=col,
                        input_field=block.inputs[key],
                    )
                y += _ROW_H + _ROW_GAP
            y += _SECTION_GAP

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._footer.handle_event(event):
            return

        content = self._content_rect()
        self._scroll.set_content(self._content_height, content.height)
        self._apply_scroll_layout(content)

        if self._scroll.handle_wheel(event, rect=content):
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.goto_menu()
            return

        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            if not content.collidepoint(event.pos):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for w in self._content_widgets:
                        if isinstance(w, TextField):
                            w.focused = False
                return

        focused_field = next(
            (w for w in self._content_widgets if isinstance(w, TextField) and w.focused),
            None,
        )
        if event.type == pygame.KEYDOWN and focused_field is not None:
            if focused_field.handle_event(event):
                return

        for widget in reversed(self._content_widgets):
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                if not widget.rect.collidepoint(event.pos):
                    continue
            if widget.handle_event(event):
                if isinstance(widget, TextField):
                    for other in self._content_widgets:
                        if other is not widget and isinstance(other, TextField):
                            other.focused = False
                return

    def _save(self) -> None:
        self._error_message = ""
        cfg = self.app.config.model_copy(deep=True)
        assert self._language is not None and self._ai_model is not None

        cfg.locale.language = self._language.value  # type: ignore[assignment]
        cfg.ai.model = self._ai_model.value

        try:
            for block in self._scenario_fields:
                sid = block.scenario_id
                updates: dict[str, int] = {}
                for key, input_field in block.inputs.items():
                    updates[key] = validate_scenario_field(
                        sid, key, input_field.text, lang=self.app.lang(),
                    )
                save_scenario_settings(sid, updates)
            save_app_config(cfg)
            reload_app_config(self.app)
            self._saved_until_ms = pygame.time.get_ticks() + 2500
        except SettingsValidationError as exc:
            self._error_message = exc.message

    def _draw_section_title(
        self,
        surface: pygame.Surface,
        *,
        text: str,
        x: int,
        y: int,
    ) -> None:
        font = body_font(15)
        surf = font.render(text, True, colors.GOLD_TEXT)
        surface.blit(surf, (x, y))

    def draw(self, surface: pygame.Surface) -> None:
        skin.draw_background(surface)
        sw, sh = surface.get_width(), surface.get_height()

        skin.draw_banner_title(
            surface,
            self.app.t("settings.title"),
            center_x=sw // 2,
            y=18,
            max_width=content_width(),
        )

        content = self._content_rect(window_height=sh)
        self._scroll.set_content(self._content_height, content.height)
        self._apply_scroll_layout(content)

        panel = pygame.Rect(
            MARGIN_X,
            content.y - 8,
            content_width(),
            content.height + 16,
        )
        skin.draw_panel(surface, panel, style="stone")

        old_clip = surface.get_clip()
        surface.set_clip(content)

        scroll = self._scroll.offset
        base_y = content.y - scroll

        self._draw_section_title(
            surface,
            text=self.app.t("settings.language"),
            x=content.x,
            y=int(base_y + self._lang_title_y),
        )
        if self._language is not None:
            self._language.draw(surface)

        self._draw_section_title(
            surface,
            text=self.app.t("settings.ai_model"),
            x=content.x,
            y=int(base_y + self._model_title_y),
        )
        if self._ai_model is not None:
            self._ai_model.draw(surface)

        self._draw_section_title(
            surface,
            text=self.app.t("settings.scenarios"),
            x=content.x,
            y=int(base_y + self._scenarios_title_y),
        )

        label_font = body_font(13)
        heading_font = body_font(15)

        for block in self._scenario_fields:
            block_title_y = int(base_y + self._block_title_y[block.scenario_id])
            name = scenario_display_name(block.scenario_id, self.app.lang())
            name_surf = heading_font.render(name, True, colors.TEXT_BODY)
            surface.blit(name_surf, (content.x, block_title_y))

            for row_keys in block.rows:
                for col, key in enumerate(row_keys):
                    input_field = block.inputs[key]
                    label = self.app.t(f"settings.field.{key}")
                    if label == f"settings.field.{key}":
                        label = key
                    cell_w = self._cell_width(content)
                    cell_x = content.x + col * (cell_w + _FIELD_COL_GAP)
                    label_rect = pygame.Rect(
                        cell_x,
                        input_field.rect.y,
                        cell_w - _FIELD_INPUT_W - 4,
                        _ROW_H,
                    )
                    skin.draw_text_clipped(
                        surface,
                        label,
                        label_rect,
                        label_font,
                        colors.TEXT_MUTED,
                        align="left",
                        pad_y=6,
                    )
                    input_field.draw(surface)

        surface.set_clip(old_clip)

        track = pygame.Rect(
            panel.right - _SCROLLBAR_W - 10,
            content.y,
            _SCROLLBAR_W,
            content.height,
        )
        skin.draw_scrollbar(
            surface,
            track,
            content_height=self._scroll.content_height,
            viewport_height=self._scroll.viewport_height,
            offset=self._scroll.offset,
        )

        footer_y = sh - _FOOTER_H
        self._back_btn.rect = pygame.Rect(MARGIN_X, footer_y, 160, 40)
        self._save_btn.rect = pygame.Rect(sw - MARGIN_X - 140, footer_y, 140, 40)
        self._footer.draw(surface)

        if self._error_message:
            err_font = body_font(14)
            err_surf = err_font.render(self._error_message, True, colors.RED_FAIL)
            surface.blit(err_surf, (MARGIN_X, footer_y - 28))

        if pygame.time.get_ticks() < self._saved_until_ms:
            ok_font = body_font(14)
            ok_surf = ok_font.render(self.app.t("settings.saved"), True, colors.TEAL_ACCENT)
            surface.blit(ok_surf, (sw // 2 - ok_surf.get_width() // 2, footer_y - 28))
