"""Scenario selection and run setup."""

from __future__ import annotations

from pathlib import Path

import pygame

from engine.core.loader import BotLoadError, load_bot
from engine.core.scenario_registry import list_scenarios
from ui.render.hud import draw_centered_text
from ui.theme import COLOR_ACCENT, COLOR_MUTED, COLOR_TEXT


class MenuScreen:
    def __init__(self, app: object) -> None:
        self.app = app
        self.scenarios = list_scenarios() or [
            {"id": "resource_wars", "name": "Resource Wars", "description": ""}
        ]
        self.selected = 0
        self.bot_path = "student_bots/example_bot.py"
        self.seed = 42
        self.error = ""
        self._editing_bot = False
        self._bot_buffer = self.bot_path

    def on_enter(self) -> None:
        self.error = ""

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if self._editing_bot:
            if event.key == pygame.K_RETURN:
                self.bot_path = self._bot_buffer.strip() or self.bot_path
                self._editing_bot = False
            elif event.key == pygame.K_ESCAPE:
                self._bot_buffer = self.bot_path
                self._editing_bot = False
            elif event.key == pygame.K_BACKSPACE:
                self._bot_buffer = self._bot_buffer[:-1]
            elif event.unicode and event.unicode.isprintable() and len(self._bot_buffer) < 80:
                self._bot_buffer += event.unicode
            return

        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected = (self.selected - 1) % len(self.scenarios)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected = (self.selected + 1) % len(self.scenarios)
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self.seed = max(0, self.seed - 1)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.seed += 1
        elif event.key == pygame.K_b:
            self._browse_bot()
        elif event.key in (pygame.K_F2, pygame.K_e):
            self._editing_bot = True
            self._bot_buffer = self.bot_path
        elif event.key == pygame.K_r:
            self.app.goto_replay()
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._start_run()
        elif event.key == pygame.K_ESCAPE:
            self.app.quit()

    def _browse_bot(self) -> None:
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            chosen = filedialog.askopenfilename(
                title="Select student bot",
                filetypes=[("Python", "*.py")],
                initialdir=str(Path.cwd() / "student_bots"),
            )
            root.destroy()
            if chosen:
                self.bot_path = chosen
                self._bot_buffer = chosen
        except Exception:
            self.error = "File browser unavailable — press E to edit bot path."

    def _start_run(self) -> None:
        self.error = ""
        bot_file = Path(self.bot_path)
        if not bot_file.is_file():
            self.error = f"Bot file not found: {self.bot_path}"
            return
        try:
            bot = load_bot(bot_file)
        except BotLoadError as exc:
            self.error = str(exc)
            return

        scenario = self.scenarios[self.selected]
        self.app.start_simulation(
            scenario_id=scenario["id"],
            bot=bot,
            bot_path=str(bot_file),
            seed=self.seed,
        )

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((24, 28, 36))
        draw_centered_text(surface, ["code-scenarios"], y_start=36, color=COLOR_ACCENT, size=28)
        draw_centered_text(
            surface,
            ["Select scenario (↑/↓)", "Seed (←/→)", "E edit bot path · B browse · R replays"],
            y_start=80,
            color=COLOR_MUTED,
            size=16,
        )

        y = 150
        font = pygame.font.SysFont("consolas,courier,monospace", 20)
        for index, scenario in enumerate(self.scenarios):
            prefix = "> " if index == self.selected else "  "
            label = f"{prefix}{scenario['name']} ({scenario['id']})"
            color = COLOR_ACCENT if index == self.selected else COLOR_TEXT
            text = font.render(label, True, color)
            surface.blit(text, (80, y))
            y += 30

        info_font = pygame.font.SysFont("consolas,courier,monospace", 16)
        bot_label = f"Bot: {self.bot_path}" if not self._editing_bot else f"Bot: {self._bot_buffer}_"
        surface.blit(info_font.render(bot_label, True, COLOR_TEXT), (80, y + 16))
        surface.blit(info_font.render(f"Seed: {self.seed}", True, COLOR_TEXT), (80, y + 40))
        surface.blit(
            info_font.render("Enter — run simulation", True, COLOR_MUTED),
            (80, y + 72),
        )

        if self.error:
            err = info_font.render(self.error, True, (255, 120, 120))
            surface.blit(err, (80, y + 100))
