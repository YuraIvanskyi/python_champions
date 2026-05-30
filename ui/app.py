"""Pygame application and screen state machine."""

from __future__ import annotations

from pathlib import Path

import pygame

from engine.core.config import load_config
from engine.core.player import Bot
from engine.i18n import translate
from engine.paths import default_results_dir, resource_path
from ui import theme
from ui.audio import BackgroundMusic, set_sound_enabled
from ui.screens.bot_guide import BotGuideScreen
from ui.screens.coach import CoachScreen
from ui.screens.menu import MenuScreen
from ui.screens.replay import ReplayScreen
from ui.screens.scores import ScoresScreen
from ui.screens.settings import SettingsScreen
from ui.screens.simulation import SimulationScreen


class App:
    def __init__(self, *, results_dir: Path | None = None, config_path: Path | None = None) -> None:
        cfg = load_config(config_path)
        self.config = cfg
        theme.apply_config(cfg.ui)
        pygame.init()
        set_sound_enabled(cfg.ui.sound_enabled)
        self.music = BackgroundMusic()
        self.music.start()
        pygame.display.set_caption("Code Scenarios")
        self._set_window_icon()
        self.screen = pygame.display.set_mode((theme.WINDOW_WIDTH, theme.WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.results_dir = results_dir or default_results_dir()
        self.pending_session_dir: Path | None = None
        self.replay_path: Path | None = None

        self.menu = MenuScreen(self)
        self.bot_guide = BotGuideScreen(self)
        self.simulation = SimulationScreen(self)
        self.scores = ScoresScreen(self)
        self.replay = ReplayScreen(self)
        self.coach = CoachScreen(self)
        self.settings = SettingsScreen(self)
        self._current = self.menu
        self._apply_locale_fonts()

    def _set_screen(self, screen: object) -> None:
        self._current = screen
        self.music.sync(screen)

    def lang(self) -> str:
        return self.config.locale.language

    def t(self, key: str, **kwargs: object) -> str:
        return translate(key, lang=self.lang(), **kwargs)

    def _apply_locale_fonts(self) -> None:
        from ui.skin import typography

        typography.apply_locale(self.config.locale.language)

    def _set_window_icon(self) -> None:
        icon_path = resource_path("ui", "assets", "icons", "char_001.png")
        try:
            icon = pygame.image.load(str(icon_path))
            pygame.display.set_icon(icon)
        except (pygame.error, FileNotFoundError, OSError):
            pass

    def goto_menu(self) -> None:
        self._set_screen(self.menu)
        self.menu.on_enter()

    def goto_bot_guide(self, scenario_id: str) -> None:
        self.bot_guide.open_scenario(scenario_id)
        self._set_screen(self.bot_guide)
        self.bot_guide.on_enter()

    def goto_replay(self) -> None:
        self.replay.replay = None
        self._set_screen(self.replay)
        self.replay.on_enter()

    def open_replay(self, path: Path) -> None:
        self._set_screen(self.replay)
        self.replay.open_path(path)
        self.music.sync(self.replay)

    def start_simulation(
        self,
        *,
        scenario_id: str,
        student_bots: list[Bot],
        seed: int,
        opponent_mode: str = "greedy",
        boss_difficulty: int | None = None,
    ) -> None:
        self.simulation.start(
            scenario_id=scenario_id,
            student_bots=student_bots,
            seed=seed,
            results_dir=self.results_dir,
            opponent_mode=opponent_mode,
            boss_difficulty=boss_difficulty,
        )
        self._set_screen(self.simulation)
        self.simulation.on_enter()

    def goto_scores(self, *, final_scores: dict[str, int], session_dir: Path | None) -> None:
        self.scores.set_results(final_scores, session_dir)
        self._set_screen(self.scores)

    def goto_coach(self, session_dir: Path, *, player_id: str | None = None) -> None:
        self.coach.open_session(session_dir, player_id=player_id)
        self._set_screen(self.coach)
        self.coach.on_enter()

    def goto_settings(self) -> None:
        self._set_screen(self.settings)
        self.settings.on_enter()

    def quit(self) -> None:
        self.running = False

    def run(self) -> None:
        self.menu.on_enter()
        self.music.sync(self.menu)
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
        self.music.stop()
        pygame.quit()


def main() -> None:
    App().run()


if __name__ == "__main__":
    main()
