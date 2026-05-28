"""Live simulation screen."""

from __future__ import annotations

import math
import threading
from pathlib import Path

import pygame

from engine.core.config import load_config
from engine.core.live_game import LiveGame
from engine.core.player import Bot
from engine.core.scenario_registry import scenario_display_name
from ui.render.action_effects import ActionEffectManager
from ui.render.hud import draw_hud, draw_toolbar_strip
from ui.render.loading_overlay import draw_loading_overlay
from ui.render.map_renderer import draw_map
from ui.skin import chrome as skin
from ui.theme import (
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
from ui.widgets import Button, WidgetGroup

_MAX_ACTION_LEN = 80


class SimulationScreen:
    AUTO_MS = 350

    def __init__(self, app: object) -> None:
        self.app = app
        self.live: LiveGame | None = None
        self.auto_mode = False
        self._auto_timer = 0
        self._finishing = False
        self._finish_go_menu = False
        self._spinner_angle = 0.0
        self._finish_thread: threading.Thread | None = None
        self._finish_result: tuple[dict[str, int], Path | None, bool] | None = None
        self._toolbar = WidgetGroup()
        self._effects = ActionEffectManager()
        self._build_toolbar()

    def _build_toolbar(self) -> None:
        placeholder = pygame.Rect(0, 0, TOOLBAR_BTN_WIDTH, TOOLBAR_HEIGHT)
        btn_kw = {"font_size": TOOLBAR_BTN_FONT}
        self._step_btn = Button(
            placeholder, "Step", on_click=self._step_once, **btn_kw,
        )
        self._play_btn = Button(
            placeholder, "Play", on_click=self._toggle_auto, **btn_kw,
        )
        self._menu_btn = Button(
            placeholder, "Menu", on_click=lambda: self._finish(go_menu=True), **btn_kw,
        )
        self._toolbar = WidgetGroup([self._step_btn, self._play_btn, self._menu_btn])

    def _layout_toolbar(self, surface: pygame.Surface) -> None:
        sw = surface.get_width()
        btn_h = TOOLBAR_HEIGHT - 10
        btn_y = toolbar_top(surface.get_height()) + 5
        w = TOOLBAR_BTN_WIDTH
        gap = TOOLBAR_BTN_GAP

        x = MARGIN_X
        for btn in (self._step_btn, self._play_btn):
            btn.rect = pygame.Rect(x, btn_y, w, btn_h)
            x += w + gap

        self._menu_btn.rect = pygame.Rect(sw - MARGIN_X - w, btn_y, w, btn_h)

    def start(
        self,
        *,
        scenario_id: str,
        student_bots: list[Bot],
        seed: int,
        results_dir: Path,
        opponent_mode: str = "greedy",
        boss_difficulty: int | None = None,
    ) -> None:
        config = load_config()
        self.live = LiveGame(
            scenario_id=scenario_id,
            student_bots=student_bots,
            seed=seed,
            config=config,
            opponent_mode=opponent_mode,
            boss_difficulty=boss_difficulty,
        )
        self.auto_mode = False
        self._auto_timer = 0
        self._effects.clear()
        self._reset_finish_state()
        self.app.pending_session_dir = None
        self.app.results_dir = results_dir

    def on_enter(self) -> None:
        self.auto_mode = False
        self._auto_timer = 0
        self._reset_finish_state()
        self._step_btn.label = self.app.t("sim.step")
        self._menu_btn.label = self.app.t("sim.menu")
        self._sync_play_label()

    def _reset_finish_state(self) -> None:
        self._finishing = False
        self._finish_go_menu = False
        self._spinner_angle = 0.0
        self._finish_thread = None
        self._finish_result = None

    def _sync_play_label(self) -> None:
        self._play_btn.label = (
            self.app.t("sim.pause") if self.auto_mode else self.app.t("sim.play")
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._finishing or self.live is None:
            return
        if self._toolbar.handle_event(event):
            return
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self._finish(go_menu=True)
        elif event.key == pygame.K_SPACE:
            self._step_once()
        elif event.key == pygame.K_a:
            self._toggle_auto()
        elif event.key == pygame.K_p:
            self._pause()

    def _toggle_auto(self) -> None:
        self.auto_mode = not self.auto_mode
        self._sync_play_label()

    def _pause(self) -> None:
        self.auto_mode = False
        self._sync_play_label()

    def update(self, dt_ms: int) -> None:
        self._effects.update(dt_ms)
        if self._finishing:
            self._spinner_angle = (self._spinner_angle + dt_ms * 0.004) % math.tau
            if self._finish_thread is not None and not self._finish_thread.is_alive():
                self._complete_finish()
            return
        if not self.auto_mode or self.live is None or self.live.is_finished():
            return
        self._auto_timer += dt_ms
        if self._auto_timer >= self.AUTO_MS:
            self._auto_timer = 0
            self._step_once()

    def _step_once(self) -> None:
        if self._finishing or self.live is None or self.live.is_finished():
            return
        turn = self.live.step()
        if turn is not None:
            self._effects.spawn_from_turn(
                turn,
                self.live.get_render_state(),
                scenario_id=self.live.scenario_id,
            )
        if self.live.is_finished():
            self._finish(go_menu=False)

    def _finish(self, *, go_menu: bool) -> None:
        if self.live is None:
            self.app.goto_menu()
            return
        if self._finishing:
            return

        self.auto_mode = False
        self._sync_play_label()
        self._finishing = True
        self._finish_go_menu = go_menu
        self._spinner_angle = 0.0
        self._finish_result = None

        live = self.live
        final_scores = live.scenario.calculate_score()
        display_scores = self._scores_with_labels(final_scores)
        results_dir = self.app.results_dir

        def _worker() -> None:
            session_dir = live.finish(
                results_dir=results_dir,
                write_results=True,
            )
            self._finish_result = (display_scores, session_dir, go_menu)

        self._finish_thread = threading.Thread(target=_worker, daemon=True)
        self._finish_thread.start()

    def _complete_finish(self) -> None:
        if self._finish_result is None:
            display_scores: dict[str, int] = {}
            session_dir: Path | None = None
            go_menu = self._finish_go_menu
        else:
            display_scores, session_dir, go_menu = self._finish_result

        self.app.pending_session_dir = session_dir
        self.live = None
        self._reset_finish_state()
        if go_menu:
            self.app.goto_menu()
        else:
            self.app.goto_scores(final_scores=display_scores, session_dir=session_dir)

    def _scores_with_labels(self, scores: dict[str, int]) -> dict[str, int]:
        if self.live is None:
            return scores
        labels: dict[str, int] = {}
        for pid, value in scores.items():
            player = self.live.players.get(pid)
            key = player.display_name if player else pid
            labels[key] = value
        return labels

    # Pixels of padding between stone frame edge and map tiles
    _FRAME_PAD = 22
    # Minimum vertical pixels reserved above the stone frame for the title banner
    _BANNER_RESERVE = 52

    def _map_origin_y(self, surface: pygame.Surface, render_state: dict) -> int:
        """Return the top-left y for map tiles, centering the framed map vertically."""
        map_rows = int(render_state["map_height"])
        pixel_h = map_rows * TILE_SIZE
        hud_y = hud_text_top()
        map_area_top = self._BANNER_RESERVE + MAP_PADDING
        map_area_bottom = hud_y - MAP_PADDING
        frame_h = pixel_h + self._FRAME_PAD * 2
        extra = max(0, map_area_bottom - map_area_top - frame_h)
        frame_top = map_area_top + extra // 2
        return frame_top + self._FRAME_PAD

    def draw(self, surface: pygame.Surface) -> None:
        skin.draw_background(surface)
        if self.live is None:
            return

        render_state = self.live.get_render_state()
        sw = surface.get_width()

        map_cols = int(render_state["map_width"])
        map_rows = int(render_state["map_height"])
        pixel_w = map_cols * TILE_SIZE
        pixel_h = map_rows * TILE_SIZE
        origin_y = self._map_origin_y(surface, render_state)
        frame_top = origin_y - self._FRAME_PAD
        origin_x = (sw - pixel_w) // 2

        # Stone frame drawn first so map tiles render on top
        frame = pygame.Rect(
            origin_x - self._FRAME_PAD,
            frame_top,
            pixel_w + self._FRAME_PAD * 2,
            pixel_h + self._FRAME_PAD * 2,
        )
        skin.draw_panel(surface, frame, style="stone")
        draw_map(surface, render_state, origin_y=origin_y, lang=self.app.lang())
        self._effects.draw(surface, origin_x=origin_x, origin_y=origin_y)

        # Decorative banner title above the stone frame
        scenario_name = scenario_display_name(self.live.scenario_id)
        banner_y = max(4, frame_top - 48)
        skin.draw_banner_title(
            surface, scenario_name,
            center_x=sw // 2,
            y=banner_y,
            max_width=content_width(sw),
        )

        names = render_state.get("display_names", {})
        last = self.live.last_turn
        action_line = ""
        if last is not None:
            parts: list[str] = []
            for pid in sorted(last.actions.keys()):
                label = names.get(pid, pid)
                parts.append(f"{label}={last.actions[pid].value}")
            action_line = self.app.t("sim.last", actions=" ".join(parts))
            if len(action_line) > _MAX_ACTION_LEN:
                action_line = action_line[:_MAX_ACTION_LEN - 1] + "…"

        labeled_scores = {
            names.get(pid, pid): score for pid, score in render_state["scores"].items()
        }
        status = self.live.status_message or self._build_status_message()
        score_str = " · ".join(f"{name}: {v}" for name, v in labeled_scores.items())
        if len(score_str) > 60:
            score_str = score_str[:57] + "…"

        hud_lines = [
            self.app.t("sim.turn", turn=render_state["turn"], scores=score_str),
            action_line,
            status,
        ]

        hud_y = hud_text_top()
        draw_hud(
            surface,
            title=scenario_name,
            subtitle=self.app.t("sim.seed", seed=self.live.seed),
            lines=hud_lines,
            y_offset=hud_y,
        )
        draw_toolbar_strip(surface, y=toolbar_top(), height=TOOLBAR_HEIGHT)
        self._layout_toolbar(surface)
        self._toolbar.draw(surface)

        if self._finishing:
            draw_loading_overlay(
                surface,
                spinner_angle=self._spinner_angle,
                lang=self.app.lang(),
            )

    def _build_status_message(self) -> str:
        if self.live is None or not self.live.is_finished():
            return self.app.t("sim.running")
        # Boss-fight end conditions
        if self.live.last_turn is not None:
            events = self.live.last_turn.events
            if "boss_defeated" in events:
                return self.app.t("sim.boss_win")
            if "party_wiped" in events:
                return self.app.t("sim.boss_lose")
        return self.app.t("sim.finished")

    def get_final_scores(self) -> dict[str, int]:
        if self.live is None:
            return {}
        return self.live.scenario.calculate_score()
