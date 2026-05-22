"""Live simulation screen."""

from __future__ import annotations

from pathlib import Path

import pygame

from engine.core.config import load_config
from engine.core.live_game import LiveGame
from engine.core.player import Bot
from ui.render.hud import draw_hud, draw_toolbar_strip
from ui.render.map_renderer import draw_map
from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font
from ui.theme import (
    FOOTER_PT,
    MAP_PADDING,
    MARGIN_X,
    TILE_SIZE,
    TOOLBAR_HEIGHT,
    content_width,
    footer_top,
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
        self._toolbar = WidgetGroup()
        self._build_toolbar()

    def _build_toolbar(self) -> None:
        y = toolbar_top()
        btn_h = TOOLBAR_HEIGHT - 8
        btn_y = y + 4
        self._step_btn = Button(pygame.Rect(24, btn_y, 88, btn_h), "Step", on_click=self._step_once)
        self._play_btn = Button(pygame.Rect(120, btn_y, 120, btn_h), "Play", on_click=self._toggle_auto)
        self._toolbar = WidgetGroup([self._step_btn, self._play_btn])

    def start(
        self,
        *,
        scenario_id: str,
        student_bots: list[Bot],
        seed: int,
        results_dir: Path,
        opponent_mode: str = "greedy",
    ) -> None:
        config = load_config()
        self.live = LiveGame(
            scenario_id=scenario_id,
            student_bots=student_bots,
            seed=seed,
            config=config,
            opponent_mode=opponent_mode,
        )
        self.auto_mode = False
        self._auto_timer = 0
        self.app.pending_session_dir = None
        self.app.results_dir = results_dir

    def on_enter(self) -> None:
        self.auto_mode = False
        self._auto_timer = 0
        self._sync_play_label()

    def _sync_play_label(self) -> None:
        self._play_btn.label = "Pause" if self.auto_mode else "Play"

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.live is None:
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
        if not self.auto_mode or self.live is None or self.live.is_finished():
            return
        self._auto_timer += dt_ms
        if self._auto_timer >= self.AUTO_MS:
            self._auto_timer = 0
            self._step_once()

    def _step_once(self) -> None:
        if self.live is None or self.live.is_finished():
            return
        self.live.step()
        if self.live.is_finished():
            self._finish(go_menu=False)

    def _finish(self, *, go_menu: bool) -> None:
        if self.live is None:
            self.app.goto_menu()
            return
        final_scores = self.live.scenario.calculate_score()
        display_scores = self._scores_with_labels(final_scores)
        session_dir = self.live.finish(
            results_dir=self.app.results_dir,
            write_results=True,
        )
        self.app.pending_session_dir = session_dir
        self.live = None
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
        draw_map(surface, render_state, origin_y=origin_y)

        # Decorative banner title above the stone frame
        banner_y = max(4, frame_top - 48)
        skin.draw_banner_title(
            surface, "Simulation",
            center_x=sw // 2,
            y=banner_y,
            max_width=320,
        )

        names = render_state.get("display_names", {})
        last = self.live.last_turn
        action_line = ""
        if last is not None:
            parts: list[str] = []
            for pid in sorted(last.actions.keys()):
                label = names.get(pid, pid)
                parts.append(f"{label}={last.actions[pid].value}")
            action_line = "Last: " + " ".join(parts)
            if len(action_line) > _MAX_ACTION_LEN:
                action_line = action_line[:_MAX_ACTION_LEN - 1] + "…"

        labeled_scores = {
            names.get(pid, pid): score for pid, score in render_state["scores"].items()
        }
        status = self.live.status_message or (
            "Finished" if self.live.is_finished() else "Running"
        )
        score_str = " · ".join(f"{name}: {v}" for name, v in labeled_scores.items())
        if len(score_str) > 60:
            score_str = score_str[:57] + "…"

        hud_lines = [
            f"Turn {render_state['turn']}  ·  {score_str}",
            action_line,
            status,
        ]

        hud_y = hud_text_top()
        draw_hud(surface, title="Simulation", lines=hud_lines, y_offset=hud_y)
        draw_toolbar_strip(surface, y=toolbar_top(), height=TOOLBAR_HEIGHT)
        self._toolbar.draw(surface)

        cw = content_width()
        footer_font = body_font(FOOTER_PT)
        foot_surf = footer_font.render(
            "Keyboard: Space step · A play/pause · P pause · Esc quit",
            True,
            colors.TEXT_MUTED,
        )
        old_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(MARGIN_X, footer_top() + 4, cw, FOOTER_PT + 8))
        surface.blit(foot_surf, (MARGIN_X, footer_top() + 4))
        surface.set_clip(old_clip)

    def get_final_scores(self) -> dict[str, int]:
        if self.live is None:
            return {}
        return self.live.scenario.calculate_score()
