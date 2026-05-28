"""Replay viewer for stored session replay.json files."""

from __future__ import annotations

from pathlib import Path

import pygame

from engine.core.replay import ReplaySession, list_session_dirs, load_replay
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

_MAX_LINE_LEN = 200


class ReplayScreen:
    def __init__(self, app: object) -> None:
        self.app = app
        self.sessions: list[Path] = []
        self.selected = 0
        self.replay: ReplaySession | None = None
        self.error = ""
        self._pick_mode = True
        self._session_rows: list[ListRow] = []
        self._picker_widgets = WidgetGroup()
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
        self._picker_widgets = WidgetGroup()
        self._session_rows = []
        # Inside the titled panel: content starts at panel_y(88) + header_overhead(45)
        y = 88 + 45
        row_w = content_width() - 24  # inner width (panel has 12px pad each side)
        ix = MARGIN_X + 12            # inner left edge
        for index, session in enumerate(self.sessions[:12]):
            row = ListRow(
                pygame.Rect(ix, y, row_w, 30),
                session.name,
                selected=index == self.selected,
                on_click=lambda i=index: self._select_session(i),
            )
            self._session_rows.append(row)
            self._picker_widgets.add(row)
            y += 34

        load_btn = Button(
            pygame.Rect(ix, y + 8, 130, 40),
            self.app.t("replay.load"),
            on_click=self._load_selected,
            primary=True,
        )
        back_btn = Button(
            pygame.Rect(ix + 146, y + 8, 110, 40),
            self.app.t("replay.back"),
            on_click=lambda: self.app.goto_menu(),
        )
        self._picker_widgets.add(load_btn)
        self._picker_widgets.add(back_btn)

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

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._pick_mode:
            if self._picker_widgets.handle_event(event):
                return
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w) and self.sessions:
                    self._select_session((self.selected - 1) % len(self.sessions))
                elif event.key in (pygame.K_DOWN, pygame.K_s) and self.sessions:
                    self._select_session((self.selected + 1) % len(self.sessions))
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
        cw = content_width()

        skin.draw_banner_title(
            surface,
            self.app.t("replay.title"),
            center_x=sw // 2,
            y=24,
            max_width=cw,
        )

        # Sessions panel with titled header
        panel_h = max(200, min(len(self.sessions[:12]) * 36 + 80, 540))
        panel = pygame.Rect(MARGIN_X, 88, cw, panel_h)
        skin.draw_panel_titled(surface, panel, self.app.t("replay.saved"), style="stone")

        if not self.sessions:
            draw_centered_text(
                surface,
                [
                    self.app.t("replay.empty_dir"),
                    self.app.t("replay.empty_hint"),
                ],
                y_start=panel.y + 60,
                color=colors.TEXT_MUTED,
                size=16,
            )
        else:
            self._picker_widgets.draw(surface)

        foot_font = body_font(FOOTER_PT)
        foot_surf = foot_font.render(
            self.app.t("replay.hint"), True, colors.TEXT_MUTED
        )
        foot_y = surface.get_height() - foot_surf.get_height() - 8
        old_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(MARGIN_X, foot_y, cw, FOOTER_PT + 8))
        surface.blit(foot_surf, (MARGIN_X, foot_y))
        surface.set_clip(old_clip)

        if self.error:
            draw_centered_text(surface, [self.error], y_start=panel.bottom + 16,
                               color=colors.RED_FAIL, size=16)
