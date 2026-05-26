"""Pygame application and screen state machine."""

from __future__ import annotations

from pathlib import Path

import pygame

from engine.core.config import load_config
from engine.core.player import Bot
from ui import theme
from ui.screens.bot_guide import BotGuideScreen
from ui.screens.coach import CoachScreen
from ui.screens.menu import MenuScreen
from ui.screens.replay import ReplayScreen
from ui.screens.scores import ScoresScreen
from ui.screens.simulation import SimulationScreen


class App:
    def __init__(self, *, results_dir: Path | None = None, config_path: Path | None = None) -> None:
        cfg = load_config(config_path)
        self.config = cfg
        theme.apply_config(cfg.ui)
        pygame.init()
        pygame.display.set_caption("code-scenarios")
        self.screen = pygame.display.set_mode((theme.WINDOW_WIDTH, theme.WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.results_dir = results_dir or Path("results")
        self.pending_session_dir: Path | None = None
        self.replay_path: Path | None = None

        self.menu = MenuScreen(self)
        self.bot_guide = BotGuideScreen(self)
        self.simulation = SimulationScreen(self)
        self.scores = ScoresScreen(self)
        self.replay = ReplayScreen(self)
        self.coach = CoachScreen(self)
        self._current = self.menu

    def goto_menu(self) -> None:
        self._current = self.menu
        self.menu.on_enter()

    def goto_bot_guide(self, scenario_id: str) -> None:
        self.bot_guide.open_scenario(scenario_id)
        self._current = self.bot_guide
        self.bot_guide.on_enter()

    def goto_replay(self) -> None:
        self.replay.replay = None
        self._current = self.replay
        self.replay.on_enter()

    def open_replay(self, path: Path) -> None:
        self._current = self.replay
        self.replay.open_path(path)

    def start_simulation(
        self,
        *,
        scenario_id: str,
        student_bots: list[Bot],
        seed: int,
        opponent_mode: str = "greedy",
    ) -> None:
        self.simulation.start(
            scenario_id=scenario_id,
            student_bots=student_bots,
            seed=seed,
            results_dir=self.results_dir,
            opponent_mode=opponent_mode,
        )
        self._current = self.simulation
        self.simulation.on_enter()

    def goto_scores(self, *, final_scores: dict[str, int], session_dir: Path | None) -> None:
        self.scores.set_results(final_scores, session_dir)
        self._current = self.scores

    def goto_coach(self, session_dir: Path, *, player_id: str | None = None) -> None:
        self.coach.open_session(session_dir, player_id=player_id)
        self._current = self.coach
        self.coach.on_enter()

    def quit(self) -> None:
        self.running = False

    def run(self) -> None:
        self.menu.on_enter()
        while self.running:
            dt_ms = self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                    break
                self._current.handle_event(event)

            if hasattr(self._current, "update"):
                self._current.update(dt_ms)

            self._current.draw(self.screen)
            pygame.display.flip()

        if self.simulation.live is not None:
            self.simulation.live.finish(
                results_dir=self.results_dir,
                write_results=True,
            )
        pygame.quit()


def main() -> None:
    App().run()


if __name__ == "__main__":
    main()
