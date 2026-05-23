"""Scenario selection and run setup — RPG launcher UI (Phase 2.9 overhaul)."""

from __future__ import annotations

import random
import re
from pathlib import Path
from typing import Literal

import pygame

from engine.core.config import load_config
from engine.core.loader import BotLoadError, load_bot, student_player_id_for_path
from engine.core.opponents import OPPONENT_MODES, builtin_icon_path
from engine.core.scenario_registry import list_scenarios
from scenarios.resource_wars.game import ResourceWarsScenario
from ui.render.icons import draw_menu_icon, load_icon
from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font
from ui.theme import (
    FOOTER_PT,
    MARGIN_X,
    content_width,
    footer_top,
)
from ui.widgets import Button, ListRow, TextField, WidgetGroup

_LABEL_PT = 14

LaunchMode = Literal["practice", "classroom"]

# ── 2-column layout ──────────────────────────────────────────────────────────
# Window 1024 × 800.  Left panel: x=48 w=404.  Right panel: x=460 w=516.
# Both panels: y=92 h=668.  draw_panel_titled overhead = 45 px → content y=137.
# ────────────────────────────────────────────────────────────────────────────

_LPANEL_X = MARGIN_X            # 48
_LPANEL_W = 404
_RPANEL_X = _LPANEL_X + _LPANEL_W + 8     # 460
_RPANEL_W = 1024 - MARGIN_X - _RPANEL_X   # 516
_PANEL_Y  = 92
_PANEL_H  = 668
_HDR      = 45

_LX = _LPANEL_X + 12            # 60
_RX = _RPANEL_X + 12            # 472
_CY = _PANEL_Y  + _HDR          # 137
_LW = _LPANEL_W - 24            # 380
_RW = _RPANEL_W - 24            # 492

# ── Left panel: ▲/▼ + scenario rows ─────────────────────────────────────────
_ARROW_BTN_W = 90
_ARROW_BTN_H = 28
_ARROW_BTN_X = _LX + (_LW - _ARROW_BTN_W) // 2   # centred
_UP_BTN_Y    = _CY               # 137
_SC_ROW_H    = 80                # tall rows with 4 text lines
_SC_ROW_GAP  = 6
_SC_START_Y  = _CY + _ARROW_BTN_H + 4              # 169

# ── Right panel: mode tabs ───────────────────────────────────────────────────
_TAB_H   = 36
_TAB_GAP = 6
_TAB_W   = (_RW - _TAB_GAP) // 2   # 243

# ── Bot section (shared) ─────────────────────────────────────────────────────
_CONTENT_START = _CY + _TAB_H + 12    # 185
_BOT_LABEL_Y   = _CONTENT_START        # 185
_BOT_FIELD_Y   = _BOT_LABEL_Y + 18    # 203
_BOT_FIELD_H   = 40
_AFTER_BOT_Y   = _BOT_FIELD_Y + _BOT_FIELD_H + 6   # 249

# Icon-only Browse/Folder (40 × 40 squares)
_ICON_BTN_W      = 40
_PRAC_FIELD_W    = _RW - _ICON_BTN_W - 6              # 446
_PRAC_BROWSE_X   = _RX + _PRAC_FIELD_W + 6            # 924
_CLASS_FIELD_W   = _RW - _ICON_BTN_W * 2 - 12         # 400
_CLASS_BROWSE_X  = _RX + _CLASS_FIELD_W + 6           # 878
_CLASS_FOLDER_X  = _CLASS_BROWSE_X + _ICON_BTN_W + 6  # 924

# ── Practice: opponent cards ─────────────────────────────────────────────────
_OPP_DIV_Y   = _AFTER_BOT_Y               # 249
_OPP_LABEL_Y = _OPP_DIV_Y + 12           # 261
_OPP_CARD_Y  = _OPP_LABEL_Y + 18         # 279
_OPP_CARD_H  = 56
_OPP_CARD_W  = (_RW - 8) // 2            # 242
_AFTER_OPP_Y = _OPP_CARD_Y + _OPP_CARD_H + 10   # 345

# ── Tile row (col 0 = Random, col 1-5 = preset maps) ─────────────────────────
_TILE_SIZE   = 76
_TILE_TOTAL  = 6
_TILE_MARGIN = 8
_TILE_GAP    = (_RW - 2 * _TILE_MARGIN - _TILE_TOTAL * _TILE_SIZE) // (_TILE_TOTAL - 1)  # 4
_TILE_ROW_H  = _TILE_SIZE + 16   # 92

# ── Practice: map section + action row ───────────────────────────────────────
_PRAC_MAP_DIV_Y   = _AFTER_OPP_Y                            # 345
_PRAC_MAP_LABEL_Y = _PRAC_MAP_DIV_Y + 12                    # 357
_PRAC_TILES_Y     = _PRAC_MAP_LABEL_Y + 18                  # 375
_PRAC_DIV2_Y      = _PRAC_TILES_Y + _TILE_ROW_H + 8         # 475
_PRAC_RUN_Y       = _PRAC_DIV2_Y + 10                       # 485
_PRAC_RUN_H       = 58
_PRAC_BOTTOM_Y    = _PRAC_RUN_Y + _PRAC_RUN_H + 8           # 551
_PRAC_BOTTOM_H    = 38
_PRAC_ERROR_Y     = _PRAC_BOTTOM_Y + _PRAC_BOTTOM_H + 6     # 595

# ── Classroom: map section + action row ──────────────────────────────────────
_CLASS_COUNT_Y     = _AFTER_BOT_Y                             # 249
_CLASS_MAP_DIV_Y   = _CLASS_COUNT_Y + 22 + 8                  # 279
_CLASS_MAP_LABEL_Y = _CLASS_MAP_DIV_Y + 12                    # 291
_CLASS_TILES_Y     = _CLASS_MAP_LABEL_Y + 18                  # 309
_CLASS_DIV2_Y      = _CLASS_TILES_Y + _TILE_ROW_H + 8         # 409
_CLASS_RUN_Y       = _CLASS_DIV2_Y + 10                       # 419
_CLASS_RUN_H       = 58
_CLASS_BOTTOM_Y    = _CLASS_RUN_Y + _CLASS_RUN_H + 8          # 485
_CLASS_BOTTOM_H    = 38
_CLASS_ERROR_Y     = _CLASS_BOTTOM_Y + _CLASS_BOTTOM_H + 6    # 529

# ── Bottom row button layout (View Replays + Quit) ────────────────────────────
_BOTTOM_BTN_W = (_RW - 6) // 2   # 243 each, with 6 px gap

# ── Scenario text ─────────────────────────────────────────────────────────────
_SCENARIO_FLAVOR: dict[str, str] = {
    "resource_wars": "Accursed relics litter a grid of ruins — claim them before your rivals do!",
}
_SCENARIO_TYPE: dict[str, str] = {
    "resource_wars": "Turn-based grid  ·  up to 8 players",
}
_SCENARIO_HINT: dict[str, str] = {
    "resource_wars": "Gather resources each turn  ·  50 turns  ·  highest score wins",
}

# ── Opponent display ──────────────────────────────────────────────────────────
_OPPONENT_NAMES: dict[str, str]      = {"greedy": "Rival",  "dumb": "Rookie"}
_OPPONENT_LABELS: dict[str, str]     = {"greedy": "Rival",  "dumb": "Rookie"}
_OPPONENT_SHORT_DESC: dict[str, str] = {
    "greedy": "Chases resources efficiently",
    "dumb":   "Wanders — great first win",
}

# ── Text colours for scenario rows ────────────────────────────────────────────
# Unselected rows use wood background — need warm readable colours.
_WOOD_NAME   = colors.GOLD_TEXT              # bright torch-gold name
_WOOD_TYPE   = (205, 178, 110)               # warm sandy amber type line
_WOOD_FLAVOR = (190, 168, 105)               # slightly dimmer flavor
_WOOD_HINT   = (220, 210, 165)               # warm cream hint

# Selected rows use parchment background — need dark readable colours.
_PARCH_NAME   = colors.PARCHMENT_TEXT        # very dark brown
_PARCH_TYPE   = (70, 55, 32)                 # medium dark brown
_PARCH_FLAVOR = (85, 68, 40)                 # medium-dark brown
_PARCH_HINT   = (60, 48, 30)                 # dark brown


# ── Helpers ───────────────────────────────────────────────────────────────────

def _tile_rect(col: int, row_y: int) -> pygame.Rect:
    x = _RX + _TILE_MARGIN + col * (_TILE_SIZE + _TILE_GAP)
    return pygame.Rect(x, row_y, _TILE_SIZE, _TILE_SIZE)


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
    clip_w = min(surf.get_width(), max_w)
    old_clip = surface.get_clip()
    surface.set_clip(pygame.Rect(x, y, clip_w, pt + 6))
    surface.blit(surf, (x, y))
    surface.set_clip(old_clip)


def _build_minimap_surface(seed: int) -> pygame.Surface | None:
    """Render a 100×100 preview surface from a scenario seed."""
    try:
        from engine.simulation.map import TileType

        scenario = ResourceWarsScenario(seed=seed, player_ids=["p1", "p2"])
        scenario.setup()
        m = scenario._map
        if m is None:
            return None

        _tile_colors = {
            TileType.EMPTY:    (62, 72, 94),
            TileType.RESOURCE: (72, 200, 100),
            TileType.OBSTACLE: (118, 86, 52),
        }
        size = 100
        cell = max(1, size // max(m.width, m.height))
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        surf.fill((40, 46, 60, 255))
        for ty in range(m.height):
            for tx in range(m.width):
                color = _tile_colors.get(m.get_tile(tx, ty), (62, 72, 94))
                r = pygame.Rect(tx * cell, ty * cell, max(1, cell - 1), max(1, cell - 1))
                pygame.draw.rect(surf, color, r)
        return surf
    except Exception:
        return None


# ── Scenario row widget ───────────────────────────────────────────────────────

class ScenarioRow(ListRow):
    """Tall scenario list row: name + type + flavour + hint."""

    def __init__(
        self,
        rect: pygame.Rect,
        scenario: dict,
        *,
        selected: bool = False,
        on_click=None,
    ) -> None:
        super().__init__(rect, scenario["name"], selected=selected, on_click=on_click)
        sid          = scenario.get("id", "")
        self._type   = _SCENARIO_TYPE.get(sid, "")
        self._flavor = _SCENARIO_FLAVOR.get(sid, "")
        self._hint   = _SCENARIO_HINT.get(sid, scenario.get("description", ""))

    def draw(self, surface: pygame.Surface) -> None:
        style = "parchment" if self.selected else "wood"
        skin.draw_panel(surface, self.rect, style=style)

        if self.hovered and not self.selected and self.enabled:
            ov = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            ov.fill((255, 220, 120, 28))
            surface.blit(ov, self.rect.topleft)

        if self.selected:
            bar = pygame.Rect(self.rect.x, self.rect.y, 4, self.rect.height)
            pygame.draw.rect(surface, colors.TEAL_ACCENT, bar, border_radius=2)
            pygame.draw.rect(surface, colors.TEAL_ACCENT, self.rect, 1, border_radius=6)

        old_clip = surface.get_clip()
        surface.set_clip(self.rect.inflate(-6, -4))

        sel = self.selected
        x = self.rect.x + 14
        y = self.rect.y + 7

        # Name
        prefix     = "> " if sel else "  "
        name_color = _PARCH_NAME if sel else _WOOD_NAME
        name_s     = body_font(16).render(prefix + self.label, True, name_color)
        surface.blit(name_s, (x, y))
        y += name_s.get_height() + 1

        # Type line
        if self._type:
            type_color = _PARCH_TYPE if sel else _WOOD_TYPE
            type_s     = body_font(12).render(self._type, True, type_color)
            surface.blit(type_s, (x + 12, y))
            y += type_s.get_height() + 1

        # Flavour line
        if self._flavor:
            fv_color = _PARCH_FLAVOR if sel else _WOOD_FLAVOR
            fv_s     = body_font(12).render(self._flavor, True, fv_color)
            surface.blit(fv_s, (x + 12, y))
            y += fv_s.get_height() + 1

        # Hint line
        if self._hint:
            hint_color = _PARCH_HINT if sel else _WOOD_HINT
            hint_s     = body_font(11).render(self._hint, True, hint_color)
            surface.blit(hint_s, (x + 12, y))

        surface.set_clip(old_clip)


# ── Main screen ───────────────────────────────────────────────────────────────

class MenuScreen:
    def __init__(self, app: object) -> None:
        self.app = app
        self.scenarios = list_scenarios() or [
            {"id": "resource_wars", "name": "Resource Wars", "description": ""}
        ]
        self.selected       = 0
        self.bot_paths_text = "student_bots/example_bot.py"
        self.seed           = 42
        self.opponent_mode  = "dumb"
        self.error          = ""
        self.launch_mode: LaunchMode = "practice"
        self._use_random_seed  = False
        self._selected_preset: int | None = None
        self._hovered_tile: int = -1

        try:
            cfg = load_config()
            self._preset_seeds = cfg.ui.map_presets.seeds
            self._preset_names = cfg.ui.map_presets.names
        except Exception:
            self._preset_seeds = [7, 23, 42, 58, 91]
            self._preset_names = ["The Clearing", "Obstacle Run", "Classic",
                                  "Open Field",   "The Maze"]

        self._minimap_surfs: list[pygame.Surface | None] = [
            _build_minimap_surface(s) for s in self._preset_seeds
        ]

        self._widgets: WidgetGroup = WidgetGroup()
        self._scenario_rows: list[ScenarioRow] = []
        self._opponent_cards: list[tuple[str, pygame.Rect]] = []
        self._tiles_y: int = _PRAC_TILES_Y
        self._build_widgets()

    # ── Widget construction ───────────────────────────────────────────────────

    def _build_widgets(self) -> None:
        self._widgets = WidgetGroup()
        self._scenario_rows = []
        self._opponent_cards = []

        # ── Left panel: ▲/▼ + scenarios ───────────────────────────────────
        self._up_btn = Button(
            pygame.Rect(_ARROW_BTN_X, _UP_BTN_Y, _ARROW_BTN_W, _ARROW_BTN_H),
            "",
            on_click=lambda: self._select_scenario(
                (self.selected - 1) % len(self.scenarios)
            ),
            icon="arrow_up",
            icon_size=14,
        )
        self._widgets.add(self._up_btn)

        ly = _SC_START_Y
        for index, sc in enumerate(self.scenarios):
            row = ScenarioRow(
                pygame.Rect(_LX, ly, _LW, _SC_ROW_H),
                sc,
                selected=index == self.selected,
                on_click=lambda i=index: self._select_scenario(i),
            )
            self._scenario_rows.append(row)
            self._widgets.add(row)
            ly += _SC_ROW_H + _SC_ROW_GAP

        self._down_btn = Button(
            pygame.Rect(_ARROW_BTN_X, ly + 2, _ARROW_BTN_W, _ARROW_BTN_H),
            "",
            on_click=lambda: self._select_scenario(
                (self.selected + 1) % len(self.scenarios)
            ),
            icon="arrow_down",
            icon_size=14,
        )
        self._widgets.add(self._down_btn)

        # ── Right panel: mode tabs ─────────────────────────────────────────
        self._prac_tab = Button(
            pygame.Rect(_RX, _CY, _TAB_W, _TAB_H),
            "Practice (vs AI)",
            on_click=lambda: self._set_mode("practice"),
            font_size=15,
            icon="shield",
            icon_size=18,
        )
        self._class_tab = Button(
            pygame.Rect(_RX + _TAB_W + _TAB_GAP, _CY, _TAB_W, _TAB_H),
            "Classroom Match",
            on_click=lambda: self._set_mode("classroom"),
            font_size=15,
            icon="classroom",
            icon_size=18,
        )
        self._widgets.add(self._prac_tab)
        self._widgets.add(self._class_tab)

        # ── Bot path field + icon-only Browse [+ Folder] ──────────────────
        if self.launch_mode == "practice":
            field_w  = _PRAC_FIELD_W
            browse_x = _PRAC_BROWSE_X
        else:
            field_w  = _CLASS_FIELD_W
            browse_x = _CLASS_BROWSE_X

        self._bot_field = TextField(
            pygame.Rect(_RX, _BOT_FIELD_Y, field_w, _BOT_FIELD_H),
            text=self.bot_paths_text,
            on_change=self._set_bot_paths_text,
            max_length=4000,
        )
        self._browse_btn = Button(
            pygame.Rect(browse_x, _BOT_FIELD_Y, _ICON_BTN_W, _BOT_FIELD_H),
            "",
            on_click=self._browse_bot,
            icon="folder",
            icon_size=20,
        )
        self._widgets.add(self._bot_field)
        self._widgets.add(self._browse_btn)

        if self.launch_mode == "classroom":
            self._folder_btn: Button | None = Button(
                pygame.Rect(_CLASS_FOLDER_X, _BOT_FIELD_Y, _ICON_BTN_W, _BOT_FIELD_H),
                "",
                on_click=self._browse_folder,
                icon="folder",
                icon_size=20,
            )
            self._widgets.add(self._folder_btn)
        else:
            self._folder_btn = None

        # ── Practice: opponent cards ───────────────────────────────────────
        if self.launch_mode == "practice":
            self._opponent_cards = []
            for i, mode in enumerate(OPPONENT_MODES):
                cx    = _RX + i * (_OPP_CARD_W + 8)
                crect = pygame.Rect(cx, _OPP_CARD_Y, _OPP_CARD_W, _OPP_CARD_H)
                self._opponent_cards.append((mode, crect))
                self._widgets.add(Button(
                    crect,
                    _OPPONENT_LABELS[mode],
                    on_click=lambda m=mode: self._set_opponent(m),
                    font_size=15,
                ))
        else:
            self._opponent_cards = []

        # ── Tile row y (mode-specific) ─────────────────────────────────────
        self._tiles_y = (
            _PRAC_TILES_Y if self.launch_mode == "practice" else _CLASS_TILES_Y
        )

        # ── Run Match ─────────────────────────────────────────────────────
        run_y  = _PRAC_RUN_Y  if self.launch_mode == "practice" else _CLASS_RUN_Y
        run_h  = _PRAC_RUN_H  if self.launch_mode == "practice" else _CLASS_RUN_H
        bot_y  = _PRAC_BOTTOM_Y if self.launch_mode == "practice" else _CLASS_BOTTOM_Y
        bot_h  = _PRAC_BOTTOM_H if self.launch_mode == "practice" else _CLASS_BOTTOM_H

        self._run_btn = Button(
            pygame.Rect(_RX, run_y, _RW, run_h),
            "Run Match",
            on_click=self._start_run,
            primary=True,
        )
        self._widgets.add(self._run_btn)

        # ── Bottom row: View Replays + Quit (side by side) ─────────────────
        self._replays_btn = Button(
            pygame.Rect(_RX, bot_y, _BOTTOM_BTN_W, bot_h),
            "View Replays",
            on_click=lambda: self.app.goto_replay(),
            font_size=15,
            icon="scroll",
            icon_size=18,
        )
        self._quit_btn = Button(
            pygame.Rect(_RX + _BOTTOM_BTN_W + 6, bot_y, _BOTTOM_BTN_W, bot_h),
            "Quit",
            on_click=lambda: self.app.quit(),
            font_size=15,
            icon="door",
            icon_size=18,
        )
        self._widgets.add(self._replays_btn)
        self._widgets.add(self._quit_btn)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _set_mode(self, mode: LaunchMode) -> None:
        if mode == "classroom":
            self.opponent_mode = "dumb"
        self.launch_mode = mode
        self.error = ""
        self._build_widgets()
        self._bot_field.text = self.bot_paths_text

    def _select_scenario(self, index: int) -> None:
        self.selected = index
        self._sync_scenario_selection()

    def _set_bot_paths_text(self, text: str) -> None:
        self.bot_paths_text = text

    def _set_opponent(self, mode: str) -> None:
        self.opponent_mode = mode

    def _toggle_random(self) -> None:
        self._use_random_seed = not self._use_random_seed
        if self._use_random_seed:
            self._selected_preset = None

    def _select_preset(self, preset_index: int) -> None:
        self._selected_preset = preset_index
        self._use_random_seed = False
        if preset_index < len(self._preset_seeds):
            self.seed = self._preset_seeds[preset_index]

    def _sync_scenario_selection(self) -> None:
        for i, row in enumerate(self._scenario_rows):
            row.selected = i == self.selected

    def on_enter(self) -> None:
        self.error = ""
        self._bot_field.text = self.bot_paths_text
        self._sync_scenario_selection()

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._widgets.handle_event(event):
            return

        if event.type == pygame.MOUSEMOTION:
            self._hovered_tile = -1
            for col in range(_TILE_TOTAL):
                if _tile_rect(col, self._tiles_y).collidepoint(event.pos):
                    self._hovered_tile = col
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                    break

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for col in range(_TILE_TOTAL):
                if _tile_rect(col, self._tiles_y).collidepoint(event.pos):
                    if col == 0:
                        self._toggle_random()
                    else:
                        self._select_preset(col - 1)
                    return

        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_UP, pygame.K_w):
            self._select_scenario((self.selected - 1) % len(self.scenarios))
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self._select_scenario((self.selected + 1) % len(self.scenarios))
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

    # ── File-browser helpers ──────────────────────────────────────────────────

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
                if self.launch_mode == "practice":
                    self.bot_paths_text = chosen[0]
                else:
                    joined = ", ".join(chosen)
                    self.bot_paths_text = (
                        self.bot_paths_text.rstrip(" ,") + ", " + joined
                        if self.bot_paths_text.strip()
                        else joined
                    )
                self._bot_field.text = self.bot_paths_text
        except Exception:
            self.error = "File browser unavailable — edit the path field manually."

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

    # ── Run match ─────────────────────────────────────────────────────────────

    def _start_run(self) -> None:
        self.error = ""
        run_seed = random.randint(0, 99) if self._use_random_seed else self.seed

        paths = _parse_bot_path_lines(self.bot_paths_text)
        if not paths:
            self.error = "Enter at least one bot .py path."
            return

        for path in paths:
            if not path.is_file():
                self.error = f"Bot file not found: {path}"
                return

        resolved = [p.resolve() for p in paths]
        if len(set(resolved)) != len(resolved):
            self.error = "Duplicate bot paths are not allowed."
            return

        if self.launch_mode == "practice" and len(paths) != 1:
            self.error = "Practice mode requires exactly one bot file."
            return

        if self.launch_mode == "classroom" and len(paths) < 2:
            self.error = "Classroom match requires at least 2 bot files."
            return

        _, max_p = ResourceWarsScenario.player_limits()
        if len(paths) > max_p:
            self.error = f"At most {max_p} bots for Resource Wars (got {len(paths)})."
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
            seed=run_seed,
            opponent_mode=self.opponent_mode if self.launch_mode == "practice" else None,
        )

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        skin.draw_background(surface)
        sw = surface.get_width()

        skin.draw_banner_title(
            surface, "Code Scenarios",
            center_x=sw // 2, y=18, max_width=content_width(),
        )

        # ── Left panel ────────────────────────────────────────────────────
        skin.draw_panel_titled(
            surface, pygame.Rect(_LPANEL_X, _PANEL_Y, _LPANEL_W, _PANEL_H),
            "Scenarios", style="wood",
        )
        n = len(self.scenarios)
        sc = self.scenarios[self.selected] if self.scenarios else {}
        # id tag below ▼ button
        id_y = _SC_START_Y + n * (_SC_ROW_H + _SC_ROW_GAP) + _ARROW_BTN_H + 16
        _draw_label(
            surface, f"id: {sc.get('id', '')}",
            _LX, id_y, color=colors.TEXT_MUTED, pt=12, max_w=_LW,
        )

        # ── Right panel ───────────────────────────────────────────────────
        skin.draw_panel_titled(
            surface, pygame.Rect(_RPANEL_X, _PANEL_Y, _RPANEL_W, _PANEL_H),
            "Configuration", style="stone",
        )

        # Active tab border
        for tab, mode in [
            (self._prac_tab,  "practice"),
            (self._class_tab, "classroom"),
        ]:
            if self.launch_mode == mode:
                pygame.draw.rect(surface, colors.TEAL_ACCENT, tab.rect, 2, border_radius=6)

        # Bot path label
        paths = _parse_bot_path_lines(self._bot_field.text)
        if self.launch_mode == "practice":
            bot_lbl = "Bot path  (single .py file)"
        else:
            cnt = len(paths)
            bot_lbl = f"Bot paths  —  {cnt} bot{'s' if cnt != 1 else ''} loaded"
        _draw_label(surface, bot_lbl, _RX, _BOT_LABEL_Y, max_w=_RW)

        # Tiny "Browse" / "Folder" captions above icon buttons
        cap_font = body_font(11)
        browse_x = _PRAC_BROWSE_X if self.launch_mode == "practice" else _CLASS_BROWSE_X
        for cap, cx in ([("Browse", browse_x)]
                        + ([("Folder", _CLASS_FOLDER_X)]
                           if self.launch_mode == "classroom" else [])):
            cs = cap_font.render(cap, True, colors.TEXT_MUTED)
            surface.blit(cs, (cx + (_ICON_BTN_W - cs.get_width()) // 2,
                               _BOT_FIELD_Y - 14))

        # Practice: opponent section
        if self.launch_mode == "practice":
            skin.draw_ornamental_divider(
                surface, pygame.Rect(_RX, _OPP_DIV_Y, _RW, 10)
            )
            _draw_label(surface, "Opponent", _RX, _OPP_LABEL_Y, max_w=_RW)
            self._draw_opponent_cards(surface)
            map_div_y   = _PRAC_MAP_DIV_Y
            map_label_y = _PRAC_MAP_LABEL_Y
            error_y     = _PRAC_ERROR_Y
        else:
            _draw_label(
                surface,
                "Add 2–8 student .py bots for the class match",
                _RX, _CLASS_COUNT_Y,
                color=colors.TEXT_MUTED, pt=12, max_w=_RW,
            )
            map_div_y   = _CLASS_MAP_DIV_Y
            map_label_y = _CLASS_MAP_LABEL_Y
            error_y     = _CLASS_ERROR_Y

        # Map / seed header
        skin.draw_ornamental_divider(
            surface, pygame.Rect(_RX, map_div_y, _RW, 10)
        )
        if self._use_random_seed:
            seed_lbl = "Map / Seed  —  random pick at launch"
        elif (self._selected_preset is not None
              and self._selected_preset < len(self._preset_names)):
            seed_lbl = (
                f"Map / Seed  —  "
                f"{self._preset_names[self._selected_preset]} (seed {self.seed})"
            )
        else:
            seed_lbl = f"Map / Seed  —  seed {self.seed}"
        _draw_label(surface, seed_lbl, _RX, map_label_y, max_w=_RW)

        # Divider before Run
        run_div_y = _PRAC_DIV2_Y if self.launch_mode == "practice" else _CLASS_DIV2_Y
        skin.draw_ornamental_divider(
            surface, pygame.Rect(_RX, run_div_y, _RW, 10)
        )

        # Widgets (drawn before tile row so tiles render on top)
        self._widgets.draw(surface)

        # Tile row (drawn on top of widget hit-areas)
        self._draw_tile_row(surface, self._tiles_y)

        # Error
        if self.error:
            skin.draw_text_clipped(
                surface, self.error,
                pygame.Rect(_RX, error_y, _RW, 22),
                body_font(13), colors.RED_FAIL, align="left",
            )

        # Footer
        foot_font = body_font(FOOTER_PT)
        foot_surf = foot_font.render(
            "↑↓ scenario  ·  Enter run  ·  Esc quit",
            True, colors.TEXT_MUTED,
        )
        old_clip = surface.get_clip()
        surface.set_clip(
            pygame.Rect(MARGIN_X, footer_top() + 4, content_width(), FOOTER_PT + 8)
        )
        surface.blit(foot_surf, (MARGIN_X, footer_top() + 4))
        surface.set_clip(old_clip)

    # ── Sub-drawing helpers ───────────────────────────────────────────────────

    def _draw_opponent_cards(self, surface: pygame.Surface) -> None:
        for mode, card_rect in self._opponent_cards:
            is_active = mode == self.opponent_mode
            skin.draw_panel(surface, card_rect, style="parchment" if is_active else "stone")
            if is_active:
                pygame.draw.rect(surface, colors.TEAL_ACCENT, card_rect, 2, border_radius=6)
            else:
                ov = pygame.Surface(card_rect.size, pygame.SRCALPHA)
                ov.fill((0, 0, 0, 40))
                surface.blit(ov, card_rect.topleft)

            icon_path = builtin_icon_path(mode)
            icon_surf = load_icon(icon_path, size=32) if icon_path else None
            tx = card_rect.x + 8
            if icon_surf:
                surface.blit(icon_surf,
                              (tx, card_rect.y + (card_rect.height - 32) // 2))
                tx += 40

            tc   = colors.PARCHMENT_TEXT if is_active else colors.TEXT_MUTED
            ns   = body_font(15).render(_OPPONENT_NAMES[mode], True, tc)
            surface.blit(ns, (tx, card_rect.y + 6))
            ds   = body_font(12).render(_OPPONENT_SHORT_DESC[mode], True, colors.TEXT_MUTED)
            dy   = card_rect.y + 6 + ns.get_height() + 2
            old  = surface.get_clip()
            surface.set_clip(pygame.Rect(tx, dy, card_rect.right - tx - 4, 16))
            surface.blit(ds, (tx, dy))
            surface.set_clip(old)

    def _draw_tile_row(self, surface: pygame.Surface, row_y: int) -> None:
        """Draw the 6 tiles: col 0 = Random die, cols 1-5 = map presets."""
        label_font = body_font(11)

        for col in range(_TILE_TOTAL):
            rect      = _tile_rect(col, row_y)
            hovered   = self._hovered_tile == col
            is_random = col == 0
            preset_i  = col - 1

            selected = (
                self._use_random_seed
                if is_random
                else (self._selected_preset == preset_i and not self._use_random_seed)
            )

            border_col = colors.TEAL_ACCENT if selected else (
                colors.STONE_HIGHLIGHT if hovered else (55, 62, 80)
            )

            pygame.draw.rect(surface, (38, 44, 58), rect)

            if is_random:
                ic       = colors.TEAL_ACCENT if selected else colors.TEXT_MUTED
                die_size = 48
                die_rect = pygame.Rect(
                    rect.x + (rect.width  - die_size) // 2,
                    rect.y + (rect.height - die_size) // 2,
                    die_size, die_size,
                )
                draw_menu_icon(surface, "random", die_rect, ic)
                label = "Random"
            else:
                if preset_i < len(self._minimap_surfs) and self._minimap_surfs[preset_i]:
                    inner  = rect.inflate(-4, -4)
                    scaled = pygame.transform.smoothscale(
                        self._minimap_surfs[preset_i], (inner.width, inner.height)
                    )
                    surface.blit(scaled, inner.topleft)
                else:
                    sv = (self._preset_seeds[preset_i]
                          if preset_i < len(self._preset_seeds) else preset_i)
                    fb = body_font(12).render(f"#{sv}", True, colors.TEXT_MUTED)
                    surface.blit(fb, (
                        rect.x + (rect.width  - fb.get_width())  // 2,
                        rect.y + (rect.height - fb.get_height()) // 2,
                    ))
                label = (self._preset_names[preset_i]
                         if preset_i < len(self._preset_names) else "")

            pygame.draw.rect(surface, border_col, rect, 2, border_radius=3)

            if hovered and not selected:
                ov = pygame.Surface(rect.size, pygame.SRCALPHA)
                ov.fill((255, 255, 255, 28))
                surface.blit(ov, rect.topleft)

            if label:
                lc = colors.TEAL_ACCENT if selected else colors.TEXT_MUTED
                ls = label_font.render(label, True, lc)
                lx = rect.x + (rect.width - ls.get_width()) // 2
                ly = rect.bottom + 3
                old_clip = surface.get_clip()
                surface.set_clip(pygame.Rect(rect.x, ly, rect.width, 14))
                surface.blit(ls, (lx, ly))
                surface.set_clip(old_clip)
