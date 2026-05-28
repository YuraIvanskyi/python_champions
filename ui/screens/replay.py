"""Replay viewer for stored session replay.json files."""

from __future__ import annotations

from pathlib import Path

import pygame

from engine.core.replay import (
    ReplaySession,
    delete_all_sessions,
    delete_session_dir,
    list_session_dirs,
    load_replay,
    session_list_label,
)
from engine.core.scenario_registry import scenario_display_name
from ui.render.action_effects import ActionEffectManager
from ui.render.hud import draw_centered_text, draw_hud, draw_toolbar_strip
from ui.render.map_renderer import draw_map
from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font
from ui.theme import (
    FOOTER_PT,
    MAP_PADDING,
    MARGIN_X,
    TILE_SIZE,
    TOOLBAR_BTN_FONT,
    TOOLBAR_BTN_GAP,
    TOOLBAR_BTN_WIDTH,
    TOOLBAR_HEIGHT,
    content_width,
    hud_text_top,
    toolbar_top,
)
from ui.widgets import Button, ListRow, WidgetGroup
from ui.widgets.scroll import ScrollState

_MAX_LINE_LEN = 200

_ROW_H = 34
_ROW_GAP = 4
_DELETE_BTN_W = 36
_ROW_INNER_GAP = 4
_PANEL_TOP = 88
_SCROLLBAR_W = 8
_SCROLLBAR_PAD = 4
_ACTION_BTN_H = 40
_ACTION_BTN_GAP = 12
_DELETE_ALL_W = 120
_PANEL_TITLE_PT = 15


class ReplayScreen:
    def __init__(self, app: object) -> None:
        self.app = app
        self.sessions: list[Path] = []
        self.selected = 0
        self.replay: ReplaySession | None = None
        self.error = ""
        self._pick_mode = True
        self._session_rows: list[ListRow] = []
        self._delete_buttons: list[Button] = []
        self._picker_scroll = ScrollState()
        self._picker_viewport = pygame.Rect(0, 0, 1, 1)
        self._picker_panel = pygame.Rect(0, 0, 1, 1)
        self._picker_list_area = pygame.Rect(0, 0, 1, 1)
        self._load_btn = Button(pygame.Rect(0, 0, 130, _ACTION_BTN_H), "Load")
        self._picker_back_btn = Button(pygame.Rect(0, 0, 110, _ACTION_BTN_H), "Back")
        self._delete_all_btn = Button(pygame.Rect(0, 0, 120, _ACTION_BTN_H), "Delete All")
        self._transport = WidgetGroup()
        self._effects = ActionEffectManager()
        self._build_transport()

    def _build_transport(self) -> None:
        placeholder = pygame.Rect(0, 0, TOOLBAR_BTN_WIDTH, TOOLBAR_HEIGHT)
        btn_kw = {"font_size": TOOLBAR_BTN_FONT}
        self._back_btn = Button(
            placeholder, "Back", on_click=self._step_back, **btn_kw,
        )
        self._fwd_btn = Button(
            placeholder, "Next", on_click=self._step_fwd, **btn_kw,
        )
        self._home_btn = Button(
            placeholder, "Start", on_click=self._go_home, **btn_kw,
        )
        self._end_btn = Button(
            placeholder, "End", on_click=self._go_end, **btn_kw,
        )
        self._menu_btn = Button(
            placeholder, "Menu", on_click=self._back_to_menu, **btn_kw,
        )
        self._transport = WidgetGroup(
            [self._back_btn, self._fwd_btn, self._home_btn, self._end_btn, self._menu_btn]
        )

    def _layout_transport(self, surface: pygame.Surface) -> None:
        """Reposition transport buttons along the bottom toolbar."""
        sw = surface.get_width()
        btn_h = TOOLBAR_HEIGHT - 10
        btn_y = toolbar_top(surface.get_height()) + 5
        w = TOOLBAR_BTN_WIDTH
        gap = TOOLBAR_BTN_GAP

        x = MARGIN_X
        for btn in (self._back_btn, self._fwd_btn, self._home_btn, self._end_btn):
            btn.rect = pygame.Rect(x, btn_y, w, btn_h)
            x += w + gap

        self._menu_btn.rect = pygame.Rect(sw - MARGIN_X - w, btn_y, w, btn_h)

    def _localize_toolbar(self) -> None:
        self._back_btn.label = self.app.t("replay.back")
        self._fwd_btn.label = self.app.t("replay.next")
        self._home_btn.label = self.app.t("replay.start")
        self._end_btn.label = self.app.t("replay.end")
        self._menu_btn.label = self.app.t("replay.menu")

    def on_enter(self) -> None:
        self._localize_toolbar()
        self._pick_mode = self.replay is None
        if self._pick_mode:
            self.sessions = list_session_dirs(self.app.results_dir)
            self.selected = 0
            self.error = ""
            self._rebuild_picker()

    def _rebuild_picker(self) -> None:
        self._picker_scroll.offset = 0
        self._session_rows = []
        self._delete_buttons = []
        lang = self.app.lang()

        for index, session in enumerate(self.sessions):
            label = session_list_label(session, lang)
            row = ListRow(
                pygame.Rect(0, 0, 10, _ROW_H),
                label,
                selected=index == self.selected,
                on_click=lambda i=index: self._select_session(i),
            )
            delete_btn = Button(
                pygame.Rect(0, 0, _DELETE_BTN_W, _ROW_H),
                self.app.t("replay.delete_short"),
                on_click=lambda i=index: self._delete_session(i),
                font_size=16,
            )
            delete_btn.hint = self.app.t("replay.delete")
            self._session_rows.append(row)
            self._delete_buttons.append(delete_btn)

        self._load_btn.label = self.app.t("replay.load")
        self._load_btn.on_click = self._load_selected
        self._load_btn.primary = True
        self._picker_back_btn.label = self.app.t("replay.back")
        self._picker_back_btn.on_click = lambda: self.app.goto_menu()
        self._delete_all_btn.label = self.app.t("replay.delete_all")
        self._delete_all_btn.on_click = self._delete_all_sessions
        self._delete_all_btn.enabled = bool(self.sessions)

        self._picker_list_widgets = WidgetGroup(
            self._session_rows + self._delete_buttons,
        )
        self._picker_action_widgets = WidgetGroup(
            [self._load_btn, self._picker_back_btn, self._delete_all_btn],
        )

    def _layout_picker_panel(self, surface: pygame.Surface) -> None:
        """Compute panel and scrollable list geometry (matches draw_panel_titled)."""
        sh = surface.get_height()
        cw = content_width(surface.get_width())
        foot_h = body_font(FOOTER_PT).get_height() + 16
        btn_row_bottom = sh - foot_h - 8
        panel_bottom = btn_row_bottom - _ACTION_BTN_H - 18
        panel_h = max(160, panel_bottom - _PANEL_TOP)
        self._picker_panel = pygame.Rect(MARGIN_X, _PANEL_TOP, cw, panel_h)

        inset = 3
        div_y = self._picker_panel.y + inset + _PANEL_TITLE_PT + 14 + 1
        content_top = div_y + 4 + skin.PANEL_PAD_Y
        list_w = (
            self._picker_panel.width
            - skin.PANEL_PAD_X * 2
            - _SCROLLBAR_W
            - _SCROLLBAR_PAD
        )
        list_h = self._picker_panel.bottom - content_top - skin.PANEL_PAD_Y
        self._picker_list_area = pygame.Rect(
            self._picker_panel.x + skin.PANEL_PAD_X,
            content_top,
            max(1, list_w),
            max(1, list_h),
        )

    def _apply_picker_scroll_layout(self) -> None:
        area = self._picker_list_area
        row_w = max(40, area.width - _DELETE_BTN_W - _ROW_INNER_GAP)
        delete_x = area.right - _DELETE_BTN_W
        y = area.y - self._picker_scroll.offset

        for row, delete_btn in zip(self._session_rows, self._delete_buttons, strict=True):
            row.rect = pygame.Rect(area.x, y, row_w, _ROW_H)
            delete_btn.rect = pygame.Rect(delete_x, y, _DELETE_BTN_W, _ROW_H)
            y += _ROW_H + _ROW_GAP

        self._picker_scroll.set_content(
            max(0, len(self._session_rows) * (_ROW_H + _ROW_GAP) - _ROW_GAP),
            area.height,
        )
        self._picker_viewport = area

        btn_y = self._picker_panel.bottom + 10
        ix = self._picker_panel.x + skin.PANEL_PAD_X
        self._load_btn.rect = pygame.Rect(ix, btn_y, 130, _ACTION_BTN_H)
        self._picker_back_btn.rect = pygame.Rect(
            ix + 130 + _ACTION_BTN_GAP, btn_y, 110, _ACTION_BTN_H,
        )
        self._delete_all_btn.rect = pygame.Rect(
            self._picker_panel.right - skin.PANEL_PAD_X - _DELETE_ALL_W,
            btn_y,
            _DELETE_ALL_W,
            _ACTION_BTN_H,
        )

    def _refresh_sessions(self) -> None:
        self.sessions = list_session_dirs(self.app.results_dir)
        if self.sessions:
            self.selected = min(self.selected, len(self.sessions) - 1)
        else:
            self.selected = 0
        self._rebuild_picker()

    def _delete_session(self, index: int) -> None:
        if index < 0 or index >= len(self.sessions):
            return
        target = self.sessions[index]
        replay_path = target / "replay.json"
        if getattr(self.app, "replay_path", None) == replay_path:
            self.app.replay_path = None
            self.replay = None
        delete_session_dir(target)
        self._refresh_sessions()

    def _delete_all_sessions(self) -> None:
        if not self.sessions:
            return
        self.app.replay_path = None
        self.replay = None
        delete_all_sessions(self.app.results_dir)
        self._refresh_sessions()

    def _select_session(self, index: int) -> None:
        self.selected = index
        for i, row in enumerate(self._session_rows):
            row.selected = i == index

    def _load_selected(self) -> None:
        if not self.sessions:
            return
        replay_path = self.sessions[self.selected] / "replay.json"
        self.open_path(replay_path)

    def open_path(self, path: Path) -> None:
        self.error = ""
        try:
            data = load_replay(path)
            self.replay = ReplaySession(data)
            self._pick_mode = False
            self._effects.clear()
            self.app.replay_path = path
            self.app.music.sync(self)
        except (OSError, ValueError, KeyError) as exc:
            self.error = self.app.t("replay.load_error", error=exc)
            self.replay = None
            self._pick_mode = True

    def _step_back(self) -> None:
        if self.replay is not None:
            self.replay.step_backward()
            self._effects.clear()

    def _step_fwd(self) -> None:
        if self.replay is not None:
            turn = self.replay.step_forward()
            if turn is not None:
                self._effects.spawn_from_turn(
                    turn,
                    self.replay.get_render_state(),
                    scenario_id=self.replay.scenario_id,
                )

    def _go_home(self) -> None:
        if self.replay is not None:
            self.replay.reset()
            self._effects.clear()

    def _go_end(self) -> None:
        if self.replay is not None:
            self.replay.seek(self.replay.turn_count - 1)
            self._effects.clear()

    def _back_to_menu(self) -> None:
        self.replay = None
        self._pick_mode = True
        self._effects.clear()
        self.app.goto_menu()

    def update(self, dt_ms: int) -> None:
        self._effects.update(dt_ms)

    def _picker_list_accepts_pointer(self, pos: tuple[int, int]) -> bool:
        return self._picker_list_area.collidepoint(pos)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._pick_mode:
            self._layout_picker_panel(self.app.screen)
            self._apply_picker_scroll_layout()
            if self._picker_action_widgets.handle_event(event):
                return
            if self._picker_scroll.handle_wheel(event, rect=self._picker_viewport):
                return
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                if not self._picker_list_accepts_pointer(event.pos):
                    if event.type == pygame.MOUSEMOTION:
                        for w in self._session_rows + self._delete_buttons:
                            w.hovered = False
                    return
            if self._picker_list_widgets.handle_event(event):
                return
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w) and self.sessions:
                    self._select_session((self.selected - 1) % len(self.sessions))
                elif event.key in (pygame.K_DOWN, pygame.K_s) and self.sessions:
                    self._select_session((self.selected + 1) % len(self.sessions))
                elif event.key == pygame.K_PAGEUP:
                    self._picker_scroll.scroll(-80)
                elif event.key == pygame.K_PAGEDOWN:
                    self._picker_scroll.scroll(80)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._load_selected()
                elif event.key == pygame.K_ESCAPE:
                    self.app.goto_menu()
            return

        if self.replay is None:
            return

        if self._transport.handle_event(event):
            return

        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_SPACE):
            self._step_fwd()
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self._step_back()
        elif event.key == pygame.K_HOME:
            self._go_home()
        elif event.key == pygame.K_END:
            self._go_end()
        elif event.key == pygame.K_ESCAPE:
            self.replay = None
            self._pick_mode = True
            self.on_enter()
            self.app.music.sync(self)

    def draw(self, surface: pygame.Surface) -> None:
        skin.draw_background(surface)
        if self._pick_mode:
            self._draw_picker(surface)
            return

        if self.replay is None:
            return

        render_state = self.replay.get_render_state()
        sw = surface.get_width()

        # Center the framed map in the space above the HUD (mirrors simulation layout)
        _FRAME_PAD = 22
        _BANNER_RESERVE = 52
        map_cols = int(render_state["map_width"])
        map_rows = int(render_state["map_height"])
        pixel_w = map_cols * TILE_SIZE
        pixel_h = map_rows * TILE_SIZE
        hud_y = hud_text_top()
        map_area_top = _BANNER_RESERVE + MAP_PADDING
        map_area_bottom = hud_y - MAP_PADDING
        frame_h = pixel_h + _FRAME_PAD * 2
        extra = max(0, map_area_bottom - map_area_top - frame_h)
        frame_top = map_area_top + extra // 2
        origin_y = frame_top + _FRAME_PAD
        origin_x = (sw - pixel_w) // 2

        frame = pygame.Rect(
            origin_x - _FRAME_PAD, frame_top,
            pixel_w + _FRAME_PAD * 2, frame_h,
        )
        skin.draw_panel(surface, frame, style="stone")
        draw_map(surface, render_state, origin_y=origin_y, lang=self.app.lang())
        self._effects.draw(surface, origin_x=origin_x, origin_y=origin_y)

        banner_y = max(4, frame_top - 48)
        scenario_name = scenario_display_name(self.replay.scenario_id)
        skin.draw_banner_title(
            surface, scenario_name,
            center_x=sw // 2,
            y=banner_y,
            max_width=content_width(sw),
        )

        names = render_state.get("display_names", {})
        idx = self.replay.turn_index
        total = self.replay.turn_count
        last = self.replay.last_turn
        action_line = ""
        if last is not None:
            parts: list[str] = []
            for pid in sorted(last.actions.keys()):
                label = names.get(pid, pid)
                parts.append(f"{label}={last.actions[pid].value}")
            action_line = self.app.t("sim.last", actions=" ".join(parts))
            if len(action_line) > _MAX_LINE_LEN:
                action_line = action_line[:_MAX_LINE_LEN - 1] + "…"

        labeled_scores = {
            names.get(pid, pid): score for pid, score in render_state["scores"].items()
        }
        score_str = " · ".join(f"{n}: {v}" for n, v in labeled_scores.items())

        labeled_final = {
            names.get(pid, pid): score
            for pid, score in self.replay.final_scores.items()
        }
        final_str = " · ".join(f"{n}: {v}" for n, v in labeled_final.items())

        draw_hud(
            surface,
            title=scenario_name,
            subtitle=self.app.t("sim.seed", seed=self.replay.seed),
            lines=[
                self.app.t(
                    "replay.turn_line", current=idx + 1, total=total, scores=score_str,
                ),
                action_line,
                self.app.t("replay.final_line", scores=final_str),
            ],
            y_offset=hud_text_top(),
        )
        draw_toolbar_strip(surface, y=toolbar_top(), height=TOOLBAR_HEIGHT)
        self._layout_transport(surface)

        self._transport.draw(surface)

    def _draw_picker(self, surface: pygame.Surface) -> None:
        sw = surface.get_width()
        sh = surface.get_height()
        cw = content_width(sw)

        skin.draw_banner_title(
            surface,
            self.app.t("replay.title"),
            center_x=sw // 2,
            y=24,
            max_width=cw,
        )

        self._layout_picker_panel(surface)
        skin.draw_panel_titled(
            surface,
            self._picker_panel,
            self.app.t("replay.saved"),
            style="stone",
            title_pt=_PANEL_TITLE_PT,
        )
        self._apply_picker_scroll_layout()
        area = self._picker_list_area

        if not self.sessions:
            draw_centered_text(
                surface,
                [
                    self.app.t("replay.empty_dir"),
                    self.app.t("replay.empty_hint"),
                ],
                y_start=self._picker_panel.y + 60,
                color=colors.TEXT_MUTED,
                size=16,
            )
        else:
            old_clip = surface.get_clip()
            surface.set_clip(area)
            for row, delete_btn in zip(
                self._session_rows, self._delete_buttons, strict=True,
            ):
                row.draw(surface)
                delete_btn.draw(surface)
            surface.set_clip(old_clip)

            if self._picker_scroll.max_offset > 0:
                track = pygame.Rect(
                    area.right + _SCROLLBAR_PAD,
                    area.y,
                    _SCROLLBAR_W,
                    area.height,
                )
                skin.draw_scrollbar(
                    surface,
                    track,
                    content_height=self._picker_scroll.content_height,
                    viewport_height=self._picker_scroll.viewport_height,
                    offset=self._picker_scroll.offset,
                )

        self._load_btn.draw(surface)
        self._picker_back_btn.draw(surface)
        self._delete_all_btn.draw(surface)

        foot_font = body_font(FOOTER_PT)
        foot_surf = foot_font.render(
            self.app.t("replay.hint"), True, colors.TEXT_MUTED
        )
        foot_y = sh - foot_surf.get_height() - 8
        surface.blit(foot_surf, (MARGIN_X, foot_y))

        if self.error:
            draw_centered_text(
                surface,
                [self.error],
                y_start=self._picker_panel.bottom + 56,
                color=colors.RED_FAIL,
                size=16,
            )
