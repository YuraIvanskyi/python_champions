"""Scenario selection and run setup."""

from __future__ import annotations

from pathlib import Path

import pygame

from engine.core.loader import BotLoadError, load_bot
from engine.core.opponents import OPPONENT_MODES, opponent_button_label, opponent_description
from engine.core.scenario_registry import list_scenarios
from ui.render.hud import draw_centered_text
from ui.theme import (
    COLOR_ACCENT,
    COLOR_BG,
    COLOR_MUTED,
    MARGIN_X,
    content_width,
    footer_top,
)
from ui.widgets import Button, ListRow, Stepper, TextField, WidgetGroup


class MenuScreen:
    def __init__(self, app: object) -> None:
        self.app = app
        self.scenarios = list_scenarios() or [
            {"id": "resource_wars", "name": "Resource Wars", "description": ""}
        ]
        self.selected = 0
        self.bot_path = "student_bots/example_bot.py"
        self.seed = 42
        self.opponent_mode = "dumb"
        self.error = ""
        self._widgets = WidgetGroup()
        self._scenario_rows: list[ListRow] = []
        self._opponent_buttons: list[Button] = []
        self._opponent_hint_y = 0
        self._build_widgets()

    def _build_widgets(self) -> None:
        self._widgets = WidgetGroup()
        self._scenario_rows = []
        width = content_width()
        x = MARGIN_X
        y = 100

        for index, scenario in enumerate(self.scenarios):
            row = ListRow(
                pygame.Rect(x, y, width, 30),
                f"{scenario['name']} ({scenario['id']})",
                selected=index == self.selected,
                on_click=lambda i=index: self._select_scenario(i),
            )
            self._scenario_rows.append(row)
            self._widgets.add(row)
            y += 34

        y += 20
        self._bot_label_y = y
        y += 22
        self._bot_field = TextField(
            pygame.Rect(x, y, width - 108, 36),
            text=self.bot_path,
            on_change=self._set_bot_path,
        )
        self._widgets.add(self._bot_field)
        self._browse_btn = Button(
            pygame.Rect(x + width - 100, y, 100, 36),
            "Browse…",
            on_click=self._browse_bot,
        )
        self._widgets.add(self._browse_btn)

        y += 52
        self._seed_label_y = y
        y += 22
        self._seed_stepper = Stepper(
            pygame.Rect(x, y, 180, 36),
            value=self.seed,
            on_change=self._set_seed,
        )
        self._widgets.add(self._seed_stepper)

        y += 52
        self._opponent_label_y = y
        y += 22
        self._opponent_buttons = []
        btn_w = width
        for mode in OPPONENT_MODES:
            btn = Button(
                pygame.Rect(x, y, btn_w, 36),
                opponent_button_label(mode),
                on_click=lambda m=mode: self._set_opponent(m),
            )
            self._opponent_buttons.append(btn)
            self._widgets.add(btn)
            y += 42

        self._opponent_hint_y = y + 4
        y += 36

        self._run_btn = Button(pygame.Rect(x, y, 150, 42), "Run", on_click=self._start_run)
        self._replays_btn = Button(
            pygame.Rect(x + 166, y, 150, 42),
            "Replays",
            on_click=lambda: self.app.goto_replay(),
        )
        self._widgets.add(self._run_btn)
        self._widgets.add(self._replays_btn)

    def _select_scenario(self, index: int) -> None:
        self.selected = index
        self._sync_scenario_selection()

    def _set_bot_path(self, path: str) -> None:
        self.bot_path = path

    def _set_seed(self, seed: int) -> None:
        self.seed = seed
        self._seed_stepper.set_value(seed)

    def _set_opponent(self, mode: str) -> None:
        self.opponent_mode = mode

    def _sync_scenario_selection(self) -> None:
        for index, row in enumerate(self._scenario_rows):
            row.selected = index == self.selected

    def on_enter(self) -> None:
        self.error = ""
        self._bot_field.text = self.bot_path
        self._seed_stepper.set_value(self.seed)
        self._sync_scenario_selection()

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._widgets.handle_event(event):
            return

        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_UP, pygame.K_w):
            self._select_scenario((self.selected - 1) % len(self.scenarios))
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self._select_scenario((self.selected + 1) % len(self.scenarios))
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self._set_seed(max(0, self.seed - 1))
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self._set_seed(self.seed + 1)
        elif event.key == pygame.K_RETURN:
            focused = self._widgets.focused
            if focused is self._bot_field:
                self._bot_field.focused = False
            else:
                self._start_run()
        elif event.key == pygame.K_ESCAPE:
            if self._bot_field.focused:
                self._bot_field.focused = False
            else:
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
                self._bot_field.text = chosen
        except Exception:
            self.error = "File browser unavailable — click the bot path field to edit."

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
            opponent_mode=self.opponent_mode,
        )

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_centered_text(surface, ["code-scenarios"], y_start=28, color=COLOR_ACCENT, size=30)
        draw_centered_text(
            surface,
            ["Click to play — keyboard shortcuts still work (see footer)"],
            y_start=62,
            color=COLOR_MUTED,
            size=14,
        )

        font = pygame.font.SysFont("consolas,courier,monospace", 16)
        label = pygame.font.SysFont("consolas,courier,monospace", 15)
        surface.blit(label.render("Scenario", True, COLOR_MUTED), (MARGIN_X, 88))
        surface.blit(label.render("Bot file", True, COLOR_MUTED), (MARGIN_X, self._bot_label_y))
        surface.blit(label.render("Seed", True, COLOR_MUTED), (MARGIN_X, self._seed_label_y))
        surface.blit(label.render("Opponent", True, COLOR_MUTED), (MARGIN_X, self._opponent_label_y))

        for index, btn in enumerate(self._opponent_buttons):
            mode = OPPONENT_MODES[index]
            selected = mode == self.opponent_mode
            pygame.draw.rect(
                surface,
                COLOR_ACCENT if selected else (44, 50, 62),
                btn.rect,
                2 if selected else 1,
                border_radius=4,
            )

        hint_font = pygame.font.SysFont("consolas,courier,monospace", 14)
        hint = hint_font.render(opponent_description(self.opponent_mode), True, COLOR_MUTED)
        surface.blit(hint, (MARGIN_X, self._opponent_hint_y))

        self._widgets.draw(surface)

        footer = pygame.font.SysFont("consolas,courier,monospace", 13)
        surface.blit(
            footer.render(
                "Keyboard: ↑↓ scenario · ←→ seed · Enter run · Esc back",
                True,
                COLOR_MUTED,
            ),
            (MARGIN_X, footer_top()),
        )

        if self.error:
            err = font.render(self.error, True, (255, 120, 120))
            surface.blit(err, (MARGIN_X, self._run_btn.rect.bottom + 12))
