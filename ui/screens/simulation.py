"""Live simulation viewer with step and auto modes."""

from __future__ import annotations

from pathlib import Path

import pygame

from engine.core.config import load_config
from engine.core.live_game import LiveGame
from engine.core.player import Bot
from ui.render.hud import draw_hud
from ui.render.map_renderer import draw_map
from ui.theme import COLOR_BG


class SimulationScreen:
    AUTO_MS = 350

    def __init__(self, app: object) -> None:
        self.app = app
        self.live: LiveGame | None = None
        self.auto_mode = False
        self._auto_timer = 0

    def start(
        self,
        *,
        scenario_id: str,
        bot: Bot,
        seed: int,
        results_dir: Path,
    ) -> None:
        config = load_config()
        self.live = LiveGame(
            scenario_id=scenario_id,
            student_bot=bot,
            seed=seed,
            config=config,
        )
        self.auto_mode = False
        self._auto_timer = 0
        self.app.pending_session_dir = None
        self.app.results_dir = results_dir

    def on_enter(self) -> None:
        self.auto_mode = False
        self._auto_timer = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN or self.live is None:
            return

        if event.key == pygame.K_ESCAPE:
            self._finish(go_menu=True)
        elif event.key == pygame.K_SPACE:
            self._step_once()
        elif event.key == pygame.K_a:
            self.auto_mode = not self.auto_mode
        elif event.key == pygame.K_p:
            self.auto_mode = False

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
        session_dir = self.live.finish(
            results_dir=self.app.results_dir,
            write_results=True,
        )
        self.app.pending_session_dir = session_dir
        self.live = None
        if go_menu:
            self.app.goto_menu()
        else:
            self.app.goto_scores(final_scores=final_scores, session_dir=session_dir)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        if self.live is None:
            return

        render_state = self.live.get_render_state()
        draw_map(surface, render_state)

        last = self.live.last_turn
        action_line = ""
        if last is not None:
            student = last.actions.get("student")
            opponent = last.actions.get("opponent")
            action_line = f"Last: student={student} opponent={opponent}"

        status = self.live.status_message or (
            "Finished" if self.live.is_finished() else "Running"
        )
        hud_lines = [
            f"Turn {render_state['turn']} / scores {render_state['scores']}",
            action_line,
            status,
        ]
        controls = "Space step · A auto · P pause · Esc quit"
        if self.auto_mode:
            controls = "AUTO · P pause · Space step · Esc quit"
        draw_hud(
            surface,
            title="Simulation",
            lines=hud_lines,
            footer=controls,
        )

    def get_final_scores(self) -> dict[str, int]:
        if self.live is None:
            return {}
        return self.live.scenario.calculate_score()
