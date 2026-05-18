"""End-of-game score screen."""

from __future__ import annotations

from pathlib import Path

import pygame

from ui.render.hud import draw_centered_text
from ui.theme import COLOR_ACCENT, COLOR_MUTED, COLOR_TEXT


class ScoresScreen:
    def __init__(self, app: object) -> None:
        self.app = app
        self.final_scores: dict[str, int] = {}
        self.session_dir: Path | None = None

    def set_results(self, final_scores: dict[str, int], session_dir: Path | None) -> None:
        self.final_scores = final_scores
        self.session_dir = session_dir

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.app.goto_menu()
        elif event.key == pygame.K_v and self.session_dir is not None:
            replay_path = self.session_dir / "replay.json"
            if replay_path.is_file():
                self.app.open_replay(replay_path)
        elif event.key == pygame.K_ESCAPE:
            self.app.goto_menu()

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((24, 28, 36))
        draw_centered_text(surface, ["Game Over"], y_start=60, color=COLOR_ACCENT, size=30)

        lines = [f"{player}: {score}" for player, score in sorted(self.final_scores.items())]
        if not lines:
            lines = ["No scores recorded"]
        draw_centered_text(surface, lines, y_start=130, color=COLOR_TEXT, size=22)

        session_line = (
            f"Session: {self.session_dir.name}" if self.session_dir else "Session not saved"
        )
        draw_centered_text(surface, [session_line], y_start=220, color=COLOR_MUTED, size=16)

        draw_centered_text(
            surface,
            ["Enter — menu", "V — view replay (if saved)"],
            y_start=300,
            color=COLOR_MUTED,
            size=16,
        )
