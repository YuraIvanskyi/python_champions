"""End-of-game score screen."""

from __future__ import annotations

from pathlib import Path

import pygame

from ui.render.hud import draw_centered_text
from ui.theme import COLOR_ACCENT, COLOR_BG, COLOR_MUTED, COLOR_TEXT, FOOTER_PT, MARGIN_X, footer_top
from ui.widgets import Button, WidgetGroup


class ScoresScreen:
    def __init__(self, app: object) -> None:
        self.app = app
        self.final_scores: dict[str, int] = {}
        self.session_dir: Path | None = None
        y = 280
        self._play_again = Button(
            pygame.Rect(120, y, 160, 40),
            "Play again",
            on_click=lambda: self.app.goto_menu(),
        )
        self._view_replay = Button(
            pygame.Rect(300, y, 160, 40),
            "View replay",
            on_click=self._open_replay,
        )
        self._open_results = Button(
            pygame.Rect(480, y, 140, 40),
            "Open folder",
            on_click=self._reveal_folder,
        )
        self._widgets = WidgetGroup([self._play_again, self._view_replay, self._open_results])

    def set_results(self, final_scores: dict[str, int], session_dir: Path | None) -> None:
        self.final_scores = final_scores
        self.session_dir = session_dir
        has_replay = session_dir is not None and (session_dir / "replay.json").is_file()
        self._view_replay.enabled = has_replay

    def _open_replay(self) -> None:
        if self.session_dir is None:
            return
        replay_path = self.session_dir / "replay.json"
        if replay_path.is_file():
            self.app.open_replay(replay_path)

    def _reveal_folder(self) -> None:
        if self.session_dir is None or not self.session_dir.is_dir():
            return
        try:
            import os
            import subprocess
            import sys

            if sys.platform == "win32":
                os.startfile(self.session_dir)  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.run(["open", str(self.session_dir)], check=False)
            else:
                subprocess.run(["xdg-open", str(self.session_dir)], check=False)
        except OSError:
            pass

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._widgets.handle_event(event):
            return
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.app.goto_menu()
        elif event.key == pygame.K_v:
            self._open_replay()
        elif event.key == pygame.K_ESCAPE:
            self.app.goto_menu()

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_centered_text(surface, ["Game Over"], y_start=60, color=COLOR_ACCENT, size=30)

        lines = [f"{player}: {score}" for player, score in sorted(self.final_scores.items())]
        if not lines:
            lines = ["No scores recorded"]
        draw_centered_text(surface, lines, y_start=130, color=COLOR_TEXT, size=22)

        session_line = (
            f"Session: {self.session_dir.name}" if self.session_dir else "Session not saved"
        )
        draw_centered_text(surface, [session_line], y_start=210, color=COLOR_MUTED, size=16)

        self._widgets.draw(surface)

        footer = pygame.font.SysFont("consolas,courier,monospace", FOOTER_PT)
        surface.blit(
            footer.render("Keyboard: Enter menu · V replay", True, COLOR_MUTED),
            (MARGIN_X, footer_top() + 4),
        )
