"""Live simulation screen."""

from __future__ import annotations

from pathlib import Path

import pygame

from engine.core.config import load_config
from engine.core.live_game import LiveGame
from engine.core.player import Bot
from ui.render.hud import draw_hud, draw_toolbar_strip
from ui.render.map_renderer import draw_map
from ui.theme import (
    COLOR_BG,
    COLOR_MUTED,
    FOOTER_PT,
    MAP_TOP,
    TOOLBAR_HEIGHT,
    footer_top,
    hud_text_top,
    toolbar_top,
)
from ui.widgets import Button, WidgetGroup


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

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        if self.live is None:
            return

        render_state = self.live.get_render_state()
        draw_map(surface, render_state, origin_y=MAP_TOP)

        names = render_state.get("display_names", {})
        last = self.live.last_turn
        action_line = ""
        if last is not None:
            parts: list[str] = []
            for pid in sorted(last.actions.keys()):
                label = names.get(pid, pid)
                parts.append(f"{label}={last.actions[pid].value}")
            action_line = "Last: " + " ".join(parts)

        labeled_scores = {
            names.get(pid, pid): score for pid, score in render_state["scores"].items()
        }
        status = self.live.status_message or (
            "Finished" if self.live.is_finished() else "Running"
        )
        hud_lines = [
            f"Turn {render_state['turn']} / scores {labeled_scores}",
            action_line,
            status,
        ]

        hud_y = hud_text_top()
        draw_hud(surface, title="Simulation", lines=hud_lines, y_offset=hud_y)
        draw_toolbar_strip(surface, y=toolbar_top(), height=TOOLBAR_HEIGHT)
        self._toolbar.draw(surface)

        footer_font = pygame.font.SysFont("consolas,courier,monospace", FOOTER_PT)
        surface.blit(
            footer_font.render(
                "Keyboard: Space step · A play/pause · P pause · Esc quit",
                True,
                COLOR_MUTED,
            ),
            (24, footer_top() + 4),
        )

    def get_final_scores(self) -> dict[str, int]:
        if self.live is None:
            return {}
        return self.live.scenario.calculate_score()
