"""Replay viewer for stored session replay.json files."""

from __future__ import annotations

from pathlib import Path

import pygame

from engine.core.replay import ReplaySession, list_session_dirs, load_replay
from ui.render.hud import draw_centered_text, draw_hud
from ui.render.map_renderer import draw_map
from ui.theme import COLOR_BG, COLOR_MUTED, COLOR_TEXT


class ReplayScreen:
    def __init__(self, app: object) -> None:
        self.app = app
        self.sessions: list[Path] = []
        self.selected = 0
        self.replay: ReplaySession | None = None
        self.error = ""
        self._pick_mode = True

    def on_enter(self) -> None:
        self._pick_mode = self.replay is None
        if self._pick_mode:
            self.sessions = list_session_dirs(self.app.results_dir)
            self.selected = 0
            self.error = ""

    def open_path(self, path: Path) -> None:
        self.error = ""
        try:
            data = load_replay(path)
            self.replay = ReplaySession(data)
            self._pick_mode = False
            self.app.replay_path = path
        except (OSError, ValueError, KeyError) as exc:
            self.error = f"Could not load replay: {exc}"
            self.replay = None
            self._pick_mode = True

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if self._pick_mode:
            if event.key in (pygame.K_UP, pygame.K_w):
                if self.sessions:
                    self.selected = (self.selected - 1) % len(self.sessions)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                if self.sessions:
                    self.selected = (self.selected + 1) % len(self.sessions)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.sessions:
                    replay_path = self.sessions[self.selected] / "replay.json"
                    self.open_path(replay_path)
            elif event.key == pygame.K_ESCAPE:
                self.app.goto_menu()
            return

        if self.replay is None:
            return

        if event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_SPACE):
            self.replay.step_forward()
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self.replay.step_backward()
        elif event.key == pygame.K_HOME:
            self.replay.reset()
        elif event.key == pygame.K_END:
            self.replay.seek(self.replay.turn_count - 1)
        elif event.key == pygame.K_ESCAPE:
            self.replay = None
            self._pick_mode = True
            self.on_enter()

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        if self._pick_mode:
            self._draw_picker(surface)
            return

        if self.replay is None:
            return

        render_state = self.replay.get_render_state()
        draw_map(surface, render_state)

        idx = self.replay.turn_index
        total = self.replay.turn_count
        last = self.replay.last_turn
        action_line = ""
        if last is not None:
            action_line = (
                f"student={last.actions['student'].value} "
                f"opponent={last.actions['opponent'].value}"
            )

        draw_hud(
            surface,
            title="Replay",
            lines=[
                f"Turn {idx + 1} / {total} · scores {render_state['scores']}",
                action_line,
                f"Final (stored): {self.replay.final_scores}",
            ],
            footer="←/→ step · Home reset · End last · Esc back",
        )

    def _draw_picker(self, surface: pygame.Surface) -> None:
        draw_centered_text(surface, ["Replay sessions"], y_start=40, size=26)
        font = pygame.font.SysFont("consolas,courier,monospace", 18)

        if not self.sessions:
            draw_centered_text(
                surface,
                ["No sessions in results/", "Run a game first (Enter on menu)"],
                y_start=120,
                color=COLOR_MUTED,
                size=16,
            )
        else:
            y = 100
            for index, session in enumerate(self.sessions[:12]):
                prefix = "> " if index == self.selected else "  "
                color = COLOR_TEXT if index == self.selected else COLOR_MUTED
                label = f"{prefix}{session.name}"
                surface.blit(font.render(label, True, color), (60, y))
                y += 28

        draw_centered_text(
            surface,
            ["Enter — load · Esc — menu"],
            y_start=surface.get_height() - 80,
            color=COLOR_MUTED,
            size=16,
        )

        if self.error:
            draw_centered_text(surface, [self.error], y_start=360, color=(255, 120, 120), size=16)
