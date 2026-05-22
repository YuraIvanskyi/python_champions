"""Scenario selection and run setup — RPG launcher UI."""

from __future__ import annotations

import re
from pathlib import Path

import pygame

from engine.core.loader import BotLoadError, load_bot, student_player_id_for_path
from engine.core.opponents import OPPONENT_MODES, opponent_button_label, opponent_description
from engine.core.scenario_registry import list_scenarios
from scenarios.resource_wars.game import ResourceWarsScenario
from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font
from ui.theme import (
    FOOTER_PT,
    MARGIN_X,
    MENU_HINT_PT,
    content_width,
    footer_top,
)
from ui.widgets import Button, ListRow, Stepper, TextField, WidgetGroup

_LABEL_PT = 14

# ── 2-column layout ────────────────────────────────────────────────────────────
# Window 1024 × 800, MARGIN_X = 48.
# Left panel (scenarios): x=48, w=404.
# Gap: 8 px.
# Right panel (configuration): x=460, w=516.
# Both panels: y=92, height=668 → bottom at y=760, footer at y=776.
#
# draw_panel_titled geometry (title_pt=15, PANEL_PAD_X=12, PANEL_PAD_Y=8):
#   inset=3, header_h=29, div_y=rect.y+33
#   content_top = rect.y + 33 + 4 + 8 = rect.y + 45
#   content_x   = rect.x + 12
# ──────────────────────────────────────────────────────────────────────────────

_LPANEL_X = MARGIN_X         # 48
_LPANEL_W = 404
_RPANEL_X = _LPANEL_X + _LPANEL_W + 8   # 460
_RPANEL_W = 1024 - MARGIN_X - _RPANEL_X  # 516
_PANEL_Y = 92
_PANEL_H = 668               # panels end at y = 760

# draw_panel_titled overhead (45 px for title_pt=15, PANEL_PAD_Y=8)
_HDR = 45

# Inner content origins for both panels
_LX = _LPANEL_X + 12         # 60
_RX = _RPANEL_X + 12         # 472
_CY = _PANEL_Y + _HDR        # 137
_LW = _LPANEL_W - 24         # 380
_RW = _RPANEL_W - 24         # 492

# Right panel widget y positions (pre-computed, must match _build_widgets)
_BOT_LABEL_Y   = _CY                       # 137
_BOT_FIELD_Y   = _BOT_LABEL_Y + 20        # 157  (14 label + 6 gap)
_BOT_FIELD_H   = 42
_BROWSE_W      = 96
_BOT_FIELD_W   = _RW - _BROWSE_W * 2 - 12 # 492 - 204 = 288  (gap=6 each side)
_BROWSE_X      = _RX + _BOT_FIELD_W + 6   # 472 + 294 = 766
_FOLDER_X      = _BROWSE_X + _BROWSE_W + 6  # 868  (868+96=964 = _RX+_RW ✓)

_SEED_LABEL_Y  = _BOT_FIELD_Y + _BOT_FIELD_H + 16   # 215
_SEED_Y        = _SEED_LABEL_Y + 20                  # 235
_SEED_W        = 220
_SEED_H        = 38

_DIV1_Y        = _SEED_Y + _SEED_H + 16             # 289
_OPP_LABEL_Y   = _DIV1_Y + 22                       # 311
_OPP_BTN_Y     = _OPP_LABEL_Y + 22                  # 333
_OPP_BTN_H     = 40
_OPP_HINT_Y    = _OPP_BTN_Y + _OPP_BTN_H + 8       # 381
_DIV2_Y        = _OPP_HINT_Y + 20 + 12              # 413
_RUN_Y         = _DIV2_Y + 23                        # 436
_RUN_H         = 72
_REPLAYS_Y     = _RUN_Y + _RUN_H + 12               # 520
_REPLAYS_H     = 44
_ERROR_Y       = _REPLAYS_Y + _REPLAYS_H + 12       # 576
_KBD_HINT_Y    = _ERROR_Y + 26                      # 602


def _parse_bot_path_lines(text: str) -> list[Path]:
    parts = re.split(r"[\n;,]+", text)
    return [Path(p.strip()) for p in parts if p.strip()]


def _draw_label(
    surface: pygame.Surface,
    text: str,
    x: int,
    y: int,
    *,
    color: tuple[int, int, int] = colors.GOLD_TEXT,
    pt: int = _LABEL_PT,
    max_w: int = 600,
) -> None:
    font = body_font(pt)
    surf = font.render(text, True, color)
    if surf.get_width() > max_w:
        old_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(x, y, max_w, pt + 4))
        surface.blit(surf, (x, y))
        surface.set_clip(old_clip)
    else:
        surface.blit(surf, (x, y))


class MenuScreen:
    def __init__(self, app: object) -> None:
        self.app = app
        self.scenarios = list_scenarios() or [
            {"id": "resource_wars", "name": "Resource Wars", "description": ""}
        ]
        self.selected = 0
        self.bot_paths_text = "student_bots/example_bot.py"
        self.seed = 42
        self.opponent_mode = "dumb"
        self.error = ""
        self._widgets = WidgetGroup()
        self._scenario_rows: list[ListRow] = []
        self._opponent_buttons: list[Button] = []
        self._build_widgets()

    def _build_widgets(self) -> None:
        self._widgets = WidgetGroup()
        self._scenario_rows = []

        # ── Left panel: scenario list ──────────────────────────────────────────
        ly = _CY
        row_h, row_gap = 38, 6
        for index, scenario in enumerate(self.scenarios):
            row = ListRow(
                pygame.Rect(_LX, ly, _LW, row_h),
                scenario["name"],
                selected=index == self.selected,
                on_click=lambda i=index: self._select_scenario(i),
            )
            self._scenario_rows.append(row)
            self._widgets.add(row)
            ly += row_h + row_gap

        # ── Right panel: configuration ─────────────────────────────────────────
        # Bot path(s) row
        self._bot_field = TextField(
            pygame.Rect(_RX, _BOT_FIELD_Y, _BOT_FIELD_W, _BOT_FIELD_H),
            text=self.bot_paths_text,
            on_change=self._set_bot_paths_text,
            max_length=4000,
        )
        self._browse_btn = Button(
            pygame.Rect(_BROWSE_X, _BOT_FIELD_Y, _BROWSE_W, _BOT_FIELD_H),
            "Browse…",
            on_click=self._browse_bot,
        )
        self._folder_btn = Button(
            pygame.Rect(_FOLDER_X, _BOT_FIELD_Y, _BROWSE_W, _BOT_FIELD_H),
            "Folder…",
            on_click=self._browse_folder,
        )
        self._widgets.add(self._bot_field)
        self._widgets.add(self._browse_btn)
        self._widgets.add(self._folder_btn)

        # Seed stepper
        self._seed_stepper = Stepper(
            pygame.Rect(_RX, _SEED_Y, _SEED_W, _SEED_H),
            value=self.seed,
            on_change=self._set_seed,
        )
        self._widgets.add(self._seed_stepper)

        # Opponent buttons (horizontal, one per mode)
        n = len(OPPONENT_MODES)
        gap = 6
        opp_w = (_RW - gap * (n - 1)) // n
        self._opponent_buttons = []
        for i, mode in enumerate(OPPONENT_MODES):
            btn = Button(
                pygame.Rect(_RX + i * (opp_w + gap), _OPP_BTN_Y, opp_w, _OPP_BTN_H),
                opponent_button_label(mode),
                on_click=lambda m=mode: self._set_opponent(m),
            )
            self._opponent_buttons.append(btn)
            self._widgets.add(btn)

        # Run Match — full inner width, prominent primary action
        self._run_btn = Button(
            pygame.Rect(_RX, _RUN_Y, _RW, _RUN_H),
            "Run Match",
            on_click=self._start_run,
            primary=True,
        )
        self._widgets.add(self._run_btn)

        # View Replays — secondary action
        self._replays_btn = Button(
            pygame.Rect(_RX, _REPLAYS_Y, 220, _REPLAYS_H),
            "View Replays",
            on_click=lambda: self.app.goto_replay(),
        )
        self._widgets.add(self._replays_btn)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _select_scenario(self, index: int) -> None:
        self.selected = index
        self._sync_scenario_selection()

    def _set_bot_paths_text(self, text: str) -> None:
        self.bot_paths_text = text

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
        self._bot_field.text = self.bot_paths_text
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
            if self._widgets.focused is self._bot_field:
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
            chosen = filedialog.askopenfilenames(
                title="Select student bot(s)",
                filetypes=[("Python", "*.py")],
                initialdir=str(Path.cwd() / "student_bots"),
            )
            root.destroy()
            if chosen:
                joined = ", ".join(chosen)
                self.bot_paths_text = (
                    self.bot_paths_text.rstrip(" ,") + ", " + joined
                    if self.bot_paths_text.strip()
                    else joined
                )
                self._bot_field.text = self.bot_paths_text
        except Exception:
            self.error = "File browser unavailable — edit the bot path(s) field manually."

    def _browse_folder(self) -> None:
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            chosen = filedialog.askdirectory(
                initialdir=str(Path.cwd() / "student_bots"),
            )
            root.destroy()
            if chosen:
                _, cap = ResourceWarsScenario.player_limits()
                py_files = sorted(Path(chosen).glob("*.py"))[:cap]
                self.bot_paths_text = ", ".join(str(p) for p in py_files)
                self._bot_field.text = self.bot_paths_text
        except Exception:
            self.error = "Folder browser unavailable — paste paths into the field."

    def _start_run(self) -> None:
        self.error = ""
        paths = _parse_bot_path_lines(self.bot_paths_text)
        if not paths:
            self.error = "Enter at least one bot .py path (comma- or newline-separated)."
            return

        for path in paths:
            if not path.is_file():
                self.error = f"Bot file not found: {path}"
                return

        resolved = [p.resolve() for p in paths]
        if len(set(resolved)) != len(resolved):
            self.error = "Duplicate bot paths are not allowed."
            return

        min_p, max_p = ResourceWarsScenario.player_limits()
        if len(paths) > max_p:
            self.error = f"At most {max_p} bots for Resource Wars (got {len(paths)})."
            return

        if len(paths) >= 2 and len(paths) < min_p:
            self.error = f"Need at least {min_p} bots for a classroom match."
            return

        try:
            if len(paths) == 1:
                bots = [load_bot(paths[0])]
            else:
                bots = [
                    load_bot(path, player_id=student_player_id_for_path(path, i))
                    for i, path in enumerate(paths)
                ]
        except BotLoadError as exc:
            self.error = str(exc)
            return

        scenario = self.scenarios[self.selected]
        self.app.start_simulation(
            scenario_id=scenario["id"],
            student_bots=bots,
            seed=self.seed,
            opponent_mode=self.opponent_mode,
        )

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        skin.draw_background(surface)
        sw = surface.get_width()

        # ── Banner ────────────────────────────────────────────────────────────
        skin.draw_banner_title(
            surface,
            "Code Scenarios",
            center_x=sw // 2,
            y=18,
            max_width=content_width(),
        )

        # ── Left panel: Scenarios ─────────────────────────────────────────────
        left_rect = pygame.Rect(_LPANEL_X, _PANEL_Y, _LPANEL_W, _PANEL_H)
        skin.draw_panel_titled(surface, left_rect, "Scenarios", style="wood")

        # Scenario description below the list rows
        sc = self.scenarios[self.selected] if self.scenarios else {}
        desc = sc.get("description", "")
        desc_y = _CY + len(self.scenarios) * 44 + 8
        if desc:
            skin.draw_text_clipped(
                surface,
                desc,
                pygame.Rect(_LX, desc_y, _LW, 56),
                body_font(13),
                colors.TEXT_MUTED,
                align="left",
            )
            desc_y += 60

        # Selected scenario id tag
        _draw_label(
            surface,
            f"id: {sc.get('id', '')}",
            _LX, desc_y,
            color=colors.TEXT_MUTED,
            pt=12,
            max_w=_LW,
        )

        # ── Right panel: Configuration ────────────────────────────────────────
        right_rect = pygame.Rect(_RPANEL_X, _PANEL_Y, _RPANEL_W, _PANEL_H)
        skin.draw_panel_titled(surface, right_rect, "Configuration", style="stone")

        # Bot path label (note classroom match hint if multiple bots)
        paths = _parse_bot_path_lines(self._bot_field.text)
        bot_lbl = (
            "Bot paths  —  classroom match (built-in opponent ignored)"
            if len(paths) >= 2
            else "Bot path(s)"
        )
        _draw_label(surface, bot_lbl, _RX, _BOT_LABEL_Y, max_w=_RW)

        # Seed label
        _draw_label(surface, "Random Seed", _RX, _SEED_LABEL_Y, max_w=_RW)

        # Ornamental dividers
        skin.draw_ornamental_divider(
            surface, pygame.Rect(_RX, _DIV1_Y, _RW, 10)
        )
        skin.draw_ornamental_divider(
            surface, pygame.Rect(_RX, _DIV2_Y, _RW, 10)
        )

        # Opponent label
        _draw_label(surface, "Opponent Mode", _RX, _OPP_LABEL_Y, max_w=_RW)

        # Opponent hint
        hint_font = body_font(MENU_HINT_PT)
        hint_surf = hint_font.render(
            opponent_description(self.opponent_mode), True, colors.TEXT_MUTED
        )
        old_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(_RX, _OPP_HINT_Y, _RW, 20))
        surface.blit(hint_surf, (_RX, _OPP_HINT_Y))
        surface.set_clip(old_clip)

        # Highlight the active opponent button with a teal selection ring
        for i, btn in enumerate(self._opponent_buttons):
            if OPPONENT_MODES[i] == self.opponent_mode:
                pygame.draw.rect(surface, colors.TEAL_ACCENT, btn.rect, 2, border_radius=5)

        # Keyboard hint inside the panel (bottom area)
        kbd_font = body_font(12)
        kbd_surf = kbd_font.render(
            "↑↓ scenario  ·  ←→ seed  ·  Enter run  ·  Esc quit",
            True,
            (90, 100, 120),
        )
        old_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(_RX, _KBD_HINT_Y, _RW, 16))
        surface.blit(kbd_surf, (_RX, _KBD_HINT_Y))
        surface.set_clip(old_clip)

        # Widgets (scenario rows, text field, buttons, stepper)
        self._widgets.draw(surface)

        # Error message
        if self.error:
            err_rect = pygame.Rect(_RX, _ERROR_Y, _RW, 22)
            skin.draw_text_clipped(
                surface,
                self.error,
                err_rect,
                body_font(13),
                colors.RED_FAIL,
                align="left",
            )

        # Footer
        foot_font = body_font(FOOTER_PT)
        foot_surf = foot_font.render(
            "↑↓ scenario  ·  ←→ seed  ·  Enter run  ·  Esc quit",
            True,
            colors.TEXT_MUTED,
        )
        old_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(MARGIN_X, footer_top() + 4,
                                     content_width(), FOOTER_PT + 8))
        surface.blit(foot_surf, (MARGIN_X, footer_top() + 4))
        surface.set_clip(old_clip)
