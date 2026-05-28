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
from engine.core.scenario_registry import create_scenario
from engine.core.scenario_registry import list_scenarios
from engine.core.scenario_registry import scenario_display_name
from engine.paths import resolve_bot_path, resource_path
from ui.render.icons import draw_menu_icon, load_icon
from ui.skin import chrome as skin
from ui.skin import colors
from ui.skin.typography import body_font
from ui.theme import (
    MARGIN_X,
    content_width,
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

# ── Left panel: scenario rows ─────────────────────────────────────────────────
_SC_ROW_H    = 126               # tall rows: name + type + 2-line flavor + 2-line hint
_SC_ROW_GAP  = 8
_SC_START_Y  = _CY

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
_OPP_CARD_H  = 66
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
_PRAC_GUIDE_Y     = _PRAC_RUN_Y + _PRAC_RUN_H + 8           # 551
_PRAC_GUIDE_H     = 40
_PRAC_BOTTOM_Y    = _PRAC_GUIDE_Y + _PRAC_GUIDE_H + 8     # 599
_PRAC_BOTTOM_H    = 38
_PRAC_ERROR_Y     = _PRAC_BOTTOM_Y + _PRAC_BOTTOM_H + 6   # 643

# ── Classroom: map section + action row ──────────────────────────────────────
_CLASS_COUNT_Y     = _AFTER_BOT_Y                             # 249
_CLASS_MAP_DIV_Y   = _CLASS_COUNT_Y + 22 + 8                  # 279
_CLASS_MAP_LABEL_Y = _CLASS_MAP_DIV_Y + 12                    # 291
_CLASS_TILES_Y     = _CLASS_MAP_LABEL_Y + 18                  # 309
_CLASS_DIV2_Y      = _CLASS_TILES_Y + _TILE_ROW_H + 8         # 409
_CLASS_RUN_Y       = _CLASS_DIV2_Y + 10                       # 419
_CLASS_RUN_H       = 58
_CLASS_GUIDE_Y     = _CLASS_RUN_Y + _CLASS_RUN_H + 8        # 485
_CLASS_GUIDE_H     = 40
_CLASS_BOTTOM_Y    = _CLASS_GUIDE_Y + _CLASS_GUIDE_H + 8    # 533
_CLASS_BOTTOM_H    = 38
_CLASS_ERROR_Y     = _CLASS_BOTTOM_Y + _CLASS_BOTTOM_H + 6  # 577

# ── Bottom row button layout (Settings + View Replays + Quit) ───────────────
_BOTTOM_BTN_W = (_RW - 12) // 3   # three buttons, 6 px gaps

# ── Scenario text ─────────────────────────────────────────────────────────────
_SCENARIO_FLAVOR: dict[str, str] = {
    "resource_wars": "Accursed relics litter the ruins — claim them before your rivals do!",
    "boss_fight": "A dread titan stalks the arena — cooperate to bring it down!",
    "energy_stations": "Arcane pools shimmer across the field — drain them dry before rivals do!",
}
_SCENARIO_TYPE: dict[str, str] = {
    "resource_wars": "Turn-based grid  ·  up to 8 players",
    "boss_fight": "Cooperative PvE  ·  1–6 players vs boss",
    "energy_stations": "Competitive PvP  ·  2–8 players  ·  push & gather",
}
_SCENARIO_HINT: dict[str, str] = {
    "resource_wars": "Gather resources each turn  ·  50 turns  ·  highest score wins",
    "boss_fight": "Attack, heal, and cooperate  ·  200 turns  ·  slay the boss to win",
    "energy_stations": "GATHER from adjacent pools  ·  ATTACK pushes rivals  ·  300 turns",
}

_DEFAULT_BOT: dict[str, str] = {
    "resource_wars": "student_bots/resource_wars/example_bot.py",
    "boss_fight": "student_bots/boss_fight/boss_fight_starter.py",
    "energy_stations": "student_bots/energy_stations/energy_stations_starter.py",
}

# ── Opponent display ──────────────────────────────────────────────────────────
_OPPONENT_NAMES: dict[str, str]      = {"greedy": "Rival",  "dumb": "Rookie"}
_OPPONENT_SHORT_DESC: dict[str, str] = {
    "greedy": "Chases resources efficiently",
    "dumb":   "Wanders — great first win",
}
_BOSS_FIGHT_ALLY_DESC: dict[str, str] = {
    "greedy": "Attacks the boss and heals when hurt",
    "dumb":   "Wanders — easy warm-up",
}

_BOSS_DIFFICULTY_LEVELS = (1, 2, 3)
_BOSS_DIFFICULTY_NAMES: dict[int, str] = {
    1: "Easy",
    2: "Medium",
    3: "Hard",
}
_BOSS_DIFFICULTY_DESC: dict[int, str] = {
    1: "30 HP · 2 dmg · random target",
    2: "40 HP · 4 dmg · targets weakest",
    3: "60 HP · 5 dmg · hits 2 bots",
}
_DIFF_CARD_H = _OPP_CARD_H
_DIFF_SECTION_H = 12 + 18 + _DIFF_CARD_H + 10

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


def _build_minimap_surface(seed: int, scenario_id: str = "resource_wars") -> pygame.Surface | None:
    """Render a 100×100 preview surface from a scenario seed."""
    try:
        from engine.simulation.map import TileType

        if scenario_id == "boss_fight":
            from scenarios.boss_fight.game import BossFightScenario
            scenario = BossFightScenario(seed=seed, player_ids=["p1"])
        elif scenario_id == "energy_stations":
            from scenarios.energy_stations.game import EnergyStationsScenario
            scenario = EnergyStationsScenario(seed=seed, player_ids=["p1", "p2"])
        else:
            from scenarios.resource_wars.game import ResourceWarsScenario
            scenario = ResourceWarsScenario(seed=seed, player_ids=["p1", "p2"])

        scenario.setup()
        m = scenario._map
        if m is None:
            return None

        _tile_colors = {
            TileType.EMPTY:    (62, 72, 94),
            TileType.RESOURCE: (72, 200, 100),
            TileType.OBSTACLE: (118, 86, 52),
            TileType.STATION:  (120, 70, 180),
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


# ── Text helpers ──────────────────────────────────────────────────────────────

def _wrap_words(text: str, font: pygame.font.Font, max_w: int) -> list[str]:
    """Word-wrap *text* into lines that fit within *max_w* pixels."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = (current + " " + word).strip() if current else word
        if font.size(trial)[0] <= max_w:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [text]


# ── Scenario row widget ───────────────────────────────────────────────────────

class ScenarioRow(ListRow):
    """Tall scenario list row: name + type + flavour + hint."""

    def __init__(
        self,
        rect: pygame.Rect,
        scenario: dict,
        app: object,
        *,
        selected: bool = False,
        on_click=None,
    ) -> None:
        sid = scenario.get("id", "")
        name = scenario_display_name(sid, app.lang())  # type: ignore[attr-defined]
        super().__init__(rect, name, selected=selected, on_click=on_click)
        self._type = app.t(f"menu.type.{sid}")  # type: ignore[attr-defined]
        self._flavor = app.t(f"menu.flavor.{sid}")  # type: ignore[attr-defined]
        self._hint = app.t(f"menu.hint.{sid}")  # type: ignore[attr-defined]

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
        surface.set_clip(self.rect.inflate(-8, -6))

        sel = self.selected
        x = self.rect.x + 16
        y = self.rect.y + 10
        # Available pixel width for sub-lines (accounts for clip inset + sub-indent)
        sub_x    = x + 12
        avail_w  = self.rect.width - 32   # rect.width − left-x-offset(28) − right-clip-inset(4)

        # Name
        name_color = _PARCH_NAME if sel else _WOOD_NAME
        name_s     = body_font(17).render(self.label, True, name_color)
        surface.blit(name_s, (x, y))
        y += name_s.get_height() + 3

        # Type line (single — always short)
        if self._type:
            type_color = _PARCH_TYPE if sel else _WOOD_TYPE
            type_s     = body_font(13).render(self._type, True, type_color)
            surface.blit(type_s, (sub_x, y))
            y += type_s.get_height() + 3

        # Flavour line — word-wrapped, max 2 lines
        if self._flavor:
            fv_color = _PARCH_FLAVOR if sel else _WOOD_FLAVOR
            fv_font  = body_font(13)
            for line in _wrap_words(self._flavor, fv_font, avail_w)[:2]:
                fv_s = fv_font.render(line, True, fv_color)
                surface.blit(fv_s, (sub_x, y))
                y += fv_s.get_height() + 2
            y += 1

        # Hint line — word-wrapped, max 2 lines
        if self._hint:
            hint_color = _PARCH_HINT if sel else _WOOD_HINT
            hint_font  = body_font(12)
            for line in _wrap_words(self._hint, hint_font, avail_w)[:2]:
                hint_s = hint_font.render(line, True, hint_color)
                surface.blit(hint_s, (sub_x, y))
                y += hint_s.get_height() + 2

        surface.set_clip(old_clip)


# ── Main screen ───────────────────────────────────────────────────────────────

class MenuScreen:
    def __init__(self, app: object) -> None:
        self.app = app
        self.scenarios = list_scenarios() or [
            {"id": "resource_wars", "name": "Resource Wars", "description": ""}
        ]
        self.selected = 0
        initial_sid = self.scenarios[self.selected].get("id", "resource_wars")
        self.bot_paths_text = self._default_bot_path(initial_sid)
        self.seed           = 42
        self.opponent_mode  = "dumb"
        self.boss_difficulty = 1
        self.error          = ""
        self.launch_mode: LaunchMode = "practice"
        self._use_random_seed  = False
        self._selected_preset: int | None = None
        self._hovered_tile: int = -1

        try:
            cfg = load_config()
            self._preset_seeds = cfg.ui.map_presets.seeds
            self._preset_names = cfg.ui.map_presets.names
            self._scenario_preset_names: dict[str, list[str]] = cfg.ui.map_presets.scenario_names
        except Exception:
            self._preset_seeds = [7, 23, 42, 58, 91]
            self._preset_names = [
                "The Clearing", "Obstacle Run", "Classic", "Open Field", "The Maze"
            ]
            self._scenario_preset_names = {}

        self._minimap_cache: dict[str, list[pygame.Surface | None]] = {}
        self._minimap_cache[initial_sid] = [
            _build_minimap_surface(s, initial_sid) for s in self._preset_seeds
        ]
        self._minimap_surfs = self._minimap_cache[initial_sid]

        self._widgets: WidgetGroup = WidgetGroup()
        self._scenario_rows: list[ScenarioRow] = []
        self._opponent_cards: list[tuple[str, pygame.Rect]] = []
        self._opponent_buttons: list[tuple[str, Button]] = []
        self._difficulty_cards: list[tuple[int, pygame.Rect]] = []
        self._difficulty_buttons: list[tuple[int, Button]] = []
        self._tiles_y: int = _PRAC_TILES_Y
        self._build_widgets()

    # ── Widget construction ───────────────────────────────────────────────────

    def _current_sid(self) -> str:
        if not self.scenarios:
            return "resource_wars"
        return self.scenarios[self.selected].get("id", "resource_wars")

    def _show_boss_difficulty(self) -> bool:
        return self._current_sid() == "boss_fight"

    def _practice_map_div_y(self) -> int:
        base = _AFTER_OPP_Y
        if self._show_boss_difficulty():
            return base + _DIFF_SECTION_H
        return base

    def _classroom_map_div_y(self) -> int:
        base = _CLASS_MAP_DIV_Y
        if self._show_boss_difficulty():
            return base + _DIFF_SECTION_H
        return base

    def _practice_run_div_y(self) -> int:
        return self._practice_map_div_y() + 12 + 18 + _TILE_ROW_H + 8

    def _classroom_run_div_y(self) -> int:
        return self._classroom_map_div_y() + 12 + 18 + _TILE_ROW_H + 8

    def _practice_error_y(self) -> int:
        run_y = self._practice_run_div_y() + 10
        guide_y = run_y + _PRAC_RUN_H + 8
        bottom_y = guide_y + _PRAC_GUIDE_H + 8
        return bottom_y + _PRAC_BOTTOM_H + 6

    def _classroom_error_y(self) -> int:
        run_y = self._classroom_run_div_y() + 10
        guide_y = run_y + _CLASS_RUN_H + 8
        bottom_y = guide_y + _CLASS_GUIDE_H + 8
        return bottom_y + _CLASS_BOTTOM_H + 6

    def _difficulty_card_y(self) -> int:
        if self.launch_mode == "practice":
            return _AFTER_OPP_Y + 12 + 18
        return _CLASS_COUNT_Y + 22 + 12 + 18

    def _map_tiles_y(self) -> int:
        if self.launch_mode == "practice":
            return self._practice_map_div_y() + 12 + 18
        return self._classroom_map_div_y() + 12 + 18

    def _default_bot_path(self, scenario_id: str) -> str:
        rel = _DEFAULT_BOT.get(
            scenario_id, "student_bots/resource_wars/example_bot.py"
        )
        return str(resolve_bot_path(rel))

    def _build_widgets(self) -> None:
        self._widgets = WidgetGroup()
        self._scenario_rows = []
        self._opponent_cards = []
        self._opponent_buttons = []
        self._difficulty_cards = []
        self._difficulty_buttons = []

        # ── Left panel: scenarios ─────────────────────────────────────────
        ly = _SC_START_Y
        for index, sc in enumerate(self.scenarios):
            row = ScenarioRow(
                pygame.Rect(_LX, ly, _LW, _SC_ROW_H),
                sc,
                self.app,
                selected=index == self.selected,
                on_click=lambda i=index: self._select_scenario(i),
            )
            self._scenario_rows.append(row)
            self._widgets.add(row)
            ly += _SC_ROW_H + _SC_ROW_GAP

        # ── Right panel: mode tabs (visuals drawn in _draw_mode_tabs) ────────
        self._prac_tab = Button(
            pygame.Rect(_RX, _CY, _TAB_W, _TAB_H),
            "",
            on_click=lambda: self._set_mode("practice"),
        )
        self._class_tab = Button(
            pygame.Rect(_RX + _TAB_W + _TAB_GAP, _CY, _TAB_W, _TAB_H),
            "",
            on_click=lambda: self._set_mode("classroom"),
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

        # ── Practice: opponent cards (visuals drawn in _draw_opponent_cards) ─
        if self.launch_mode == "practice":
            self._opponent_cards = []
            for i, mode in enumerate(OPPONENT_MODES):
                cx    = _RX + i * (_OPP_CARD_W + 8)
                crect = pygame.Rect(cx, _OPP_CARD_Y, _OPP_CARD_W, _OPP_CARD_H)
                self._opponent_cards.append((mode, crect))
                btn = Button(
                    crect,
                    "",
                    on_click=lambda m=mode: self._set_opponent(m),
                )
                self._opponent_buttons.append((mode, btn))
                self._widgets.add(btn)
        else:
            self._opponent_cards = []
            self._opponent_buttons = []

        if self._show_boss_difficulty():
            self._difficulty_cards = []
            diff_y = self._difficulty_card_y()
            gap = 8
            card_w = (_RW - gap * 2) // 3
            for i, level in enumerate(_BOSS_DIFFICULTY_LEVELS):
                cx = _RX + i * (card_w + gap)
                crect = pygame.Rect(cx, diff_y, card_w, _DIFF_CARD_H)
                self._difficulty_cards.append((level, crect))
                btn = Button(
                    crect,
                    "",
                    on_click=lambda lvl=level: self._set_boss_difficulty(lvl),
                )
                self._difficulty_buttons.append((level, btn))
                self._widgets.add(btn)

        # ── Tile row y (mode-specific) ─────────────────────────────────────
        self._tiles_y = self._map_tiles_y()

        # ── Run Match ─────────────────────────────────────────────────────
        run_y = (
            self._practice_run_div_y() + 10
            if self.launch_mode == "practice"
            else self._classroom_run_div_y() + 10
        )
        run_h  = _PRAC_RUN_H  if self.launch_mode == "practice" else _CLASS_RUN_H

        self._run_btn = Button(
            pygame.Rect(_RX, run_y, _RW, run_h),
            self.app.t("menu.run_match"),
            on_click=self._start_run,
            primary=True,
        )
        self._widgets.add(self._run_btn)

        guide_y = run_y + run_h + 8
        guide_h = _PRAC_GUIDE_H if self.launch_mode == "practice" else _CLASS_GUIDE_H
        sid = self._current_sid()
        guide_label = self.app.t(
            "menu.guide_label",
            name=scenario_display_name(sid, self.app.lang()),
        )
        self._guide_btn = Button(
            pygame.Rect(_RX, guide_y, _RW, guide_h),
            guide_label,
            on_click=self._open_bot_guide,
            font_size=14,
            icon="scroll",
            icon_size=18,
        )
        self._widgets.add(self._guide_btn)

        # ── Bottom row: Settings + View Replays + Quit ─────────────────────
        bottom_y = guide_y + guide_h + 8
        bottom_h = _PRAC_BOTTOM_H if self.launch_mode == "practice" else _CLASS_BOTTOM_H
        self._settings_btn = Button(
            pygame.Rect(_RX, bottom_y, _BOTTOM_BTN_W, bottom_h),
            self.app.t("menu.settings"),
            on_click=lambda: self.app.goto_settings(),
            font_size=15,
            icon="scroll",
            icon_size=18,
        )
        self._replays_btn = Button(
            pygame.Rect(_RX + _BOTTOM_BTN_W + 6, bottom_y, _BOTTOM_BTN_W, bottom_h),
            self.app.t("menu.view_replays"),
            on_click=lambda: self.app.goto_replay(),
            font_size=15,
            icon="scroll",
            icon_size=18,
        )
        self._quit_btn = Button(
            pygame.Rect(_RX + (_BOTTOM_BTN_W + 6) * 2, bottom_y, _BOTTOM_BTN_W, bottom_h),
            self.app.t("menu.quit"),
            on_click=lambda: self.app.quit(),
            font_size=15,
            icon="door",
            icon_size=18,
        )
        self._widgets.add(self._settings_btn)
        self._widgets.add(self._replays_btn)
        self._widgets.add(self._quit_btn)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _set_mode(self, mode: LaunchMode) -> None:
        if mode == self.launch_mode:
            return
        if mode == "classroom":
            self.opponent_mode = "dumb"
        else:
            current_sid = (
                self.scenarios[self.selected].get("id", "resource_wars")
                if self.scenarios else "resource_wars"
            )
            self.bot_paths_text = self._default_bot_path(current_sid)
        self.launch_mode = mode
        self.error = ""
        if mode == "classroom":
            self.bot_paths_text = ""
        self._build_widgets()

    def _select_scenario(self, index: int) -> None:
        self.selected = index
        self._sync_scenario_selection()
        # Rebuild minimaps for new scenario
        sid = self.scenarios[index].get("id", "resource_wars") if self.scenarios else "resource_wars"
        if sid not in self._minimap_cache:
            self._minimap_cache[sid] = [
                _build_minimap_surface(s, sid) for s in self._preset_seeds
            ]
        self._minimap_surfs = self._minimap_cache[sid]
        if self.launch_mode == "practice":
            self.bot_paths_text = self._default_bot_path(sid)
        self._build_widgets()

    def _set_bot_paths_text(self, text: str) -> None:
        self.bot_paths_text = text

    def _set_opponent(self, mode: str) -> None:
        self.opponent_mode = mode

    def _set_boss_difficulty(self, level: int) -> None:
        self.boss_difficulty = level

    def _open_bot_guide(self) -> None:
        sid = (
            self.scenarios[self.selected].get("id", "resource_wars")
            if self.scenarios else "resource_wars"
        )
        self.app.goto_bot_guide(sid)

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

    def _refresh_scenarios(self) -> None:
        raw = list_scenarios() or [
            {"id": "resource_wars", "name": "Resource Wars", "description": ""}
        ]
        lang = self.app.lang()
        self.scenarios = [
            {
                "id": entry["id"],
                "name": scenario_display_name(entry["id"], lang),
                "description": entry.get("description", ""),
            }
            for entry in raw
        ]

    def on_enter(self) -> None:
        self.error = ""
        self._refresh_scenarios()
        self._build_widgets()
        if hasattr(self, "_bot_field"):
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
                title=self.app.t("menu.file_dialog_title"),
                filetypes=[(self.app.t("menu.file_dialog_filter"), "*.py")],
                initialdir=str(resource_path("student_bots")),
            )
            root.destroy()
            if chosen:
                self.bot_paths_text = (
                    chosen[0] if self.launch_mode == "practice"
                    else ", ".join(chosen)
                )
                self._bot_field.text = self.bot_paths_text
        except Exception:
            self.error = self.app.t("menu.file_browser_unavailable")

    def _browse_folder(self) -> None:
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            chosen = filedialog.askdirectory(
                initialdir=str(resource_path("student_bots")),
            )
            root.destroy()
            if chosen:
                scenario_id = self.scenarios[self.selected].get("id", "resource_wars")
                _, cap = self._get_scenario_player_limits(scenario_id)
                py_files = sorted(Path(chosen).glob("*.py"))[:cap]
                self.bot_paths_text = ", ".join(str(p) for p in py_files)
                self._bot_field.text = self.bot_paths_text
        except Exception:
            self.error = self.app.t("menu.folder_browser_unavailable")

    def _get_scenario_player_limits(self, scenario_id: str) -> tuple[int, int]:
        try:
            sc = create_scenario(scenario_id, seed=0)
            fn = getattr(sc.__class__, "player_limits", None)
            if callable(fn):
                return fn()
        except Exception:
            pass
        from scenarios.resource_wars.game import ResourceWarsScenario
        return ResourceWarsScenario.player_limits()

    # ── Run match ─────────────────────────────────────────────────────────────

    def _start_run(self) -> None:
        self.error = ""
        run_seed = random.randint(0, 99) if self._use_random_seed else self.seed

        paths = [resolve_bot_path(p) for p in _parse_bot_path_lines(self.bot_paths_text)]
        if not paths:
            self.error = self.app.t("menu.error_no_paths")
            return

        for path in paths:
            if not path.is_file():
                self.error = self.app.t("menu.error_not_found", path=path)
                return

        resolved = [p.resolve() for p in paths]
        if len(set(resolved)) != len(resolved):
            self.error = self.app.t("menu.error_duplicate")
            return

        scenario_id = self.scenarios[self.selected].get("id", "resource_wars")
        min_p, max_p = self._get_scenario_player_limits(scenario_id)

        if self.launch_mode == "practice" and len(paths) != 1:
            self.error = self.app.t("menu.error_practice_one")
            return

        if self.launch_mode == "classroom" and len(paths) < 2:
            self.error = self.app.t("menu.error_classroom_min")
            return

        if len(paths) > max_p:
            self.error = self.app.t(
                "menu.error_max_bots",
                max_p=max_p,
                scenario_id=scenario_id,
                count=len(paths),
            )
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

        self.app.start_simulation(
            scenario_id=scenario_id,
            student_bots=bots,
            seed=run_seed,
            opponent_mode=self.opponent_mode if self.launch_mode == "practice" else None,
            boss_difficulty=self.boss_difficulty if scenario_id == "boss_fight" else None,
        )

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        skin.draw_background(surface)
        sw = surface.get_width()

        skin.draw_banner_title(
            surface, self.app.t("menu.title"),
            center_x=sw // 2, y=18, max_width=content_width(),
        )

        skin.draw_panel_titled(
            surface, pygame.Rect(_LPANEL_X, _PANEL_Y, _LPANEL_W, _PANEL_H),
            self.app.t("menu.scenarios"), style="wood",
        )

        skin.draw_panel_titled(
            surface, pygame.Rect(_RPANEL_X, _PANEL_Y, _RPANEL_W, _PANEL_H),
            self.app.t("menu.configuration"), style="stone",
        )

        paths = _parse_bot_path_lines(self._bot_field.text)
        if self.launch_mode == "practice":
            bot_lbl = self.app.t("menu.bot_path_single")
        else:
            cnt = len(paths)
            plural = self.app.t("menu.bot_plural.s") if cnt != 1 else self.app.t("menu.bot_plural.empty")
            bot_lbl = self.app.t("menu.bot_paths_multi", count=cnt, plural=plural)
        _draw_label(surface, bot_lbl, _RX, _BOT_LABEL_Y, max_w=_RW)

        # Tiny "Browse" / "Folder" captions above icon buttons
        cap_font = body_font(11)
        browse_x = _PRAC_BROWSE_X if self.launch_mode == "practice" else _CLASS_BROWSE_X
        caps = [(self.app.t("menu.browse"), browse_x)]
        if self.launch_mode == "classroom":
            caps.append((self.app.t("menu.folder"), _CLASS_FOLDER_X))
        for cap, cx in caps:
            cs = cap_font.render(cap, True, colors.TEXT_MUTED)
            surface.blit(cs, (cx + (_ICON_BTN_W - cs.get_width()) // 2,
                               _BOT_FIELD_Y - 14))

        # Practice: opponent / ally section
        if self.launch_mode == "practice":
            skin.draw_ornamental_divider(
                surface, pygame.Rect(_RX, _OPP_DIV_Y, _RW, 10)
            )
            _cur_sid = self._current_sid()
            opp_name = self.app.t(f"menu.opponent.{self.opponent_mode}")
            role = (
                self.app.t("menu.ally")
                if _cur_sid == "boss_fight"
                else self.app.t("menu.opponent")
            )
            _draw_label(
                surface, f"{role}  —  {opp_name}",
                _RX, _OPP_LABEL_Y, max_w=_RW,
            )
            map_div_y = self._practice_map_div_y()
            map_label_y = map_div_y + 12
            error_y = self._practice_error_y()
        else:
            _cur_sid = self._current_sid()
            _min_p, _max_p = self._get_scenario_player_limits(_cur_sid)
            _class_hint = self.app.t(
                "menu.classroom_hint", min_p=_min_p, max_p=_max_p,
            )
            _draw_label(
                surface,
                _class_hint,
                _RX, _CLASS_COUNT_Y,
                color=colors.TEXT_MUTED, pt=12, max_w=_RW,
            )
            map_div_y = self._classroom_map_div_y()
            map_label_y = map_div_y + 12
            error_y = self._classroom_error_y()

        if self._show_boss_difficulty():
            diff_div_y = _AFTER_OPP_Y if self.launch_mode == "practice" else _CLASS_COUNT_Y + 22
            skin.draw_ornamental_divider(
                surface, pygame.Rect(_RX, diff_div_y, _RW, 10)
            )
            diff_name = self.app.t(f"menu.difficulty.{self.boss_difficulty}")
            _draw_label(
                surface,
                self.app.t("menu.boss_difficulty", name=diff_name),
                _RX,
                diff_div_y + 12,
                max_w=_RW,
            )

        # Map / seed header
        skin.draw_ornamental_divider(
            surface, pygame.Rect(_RX, map_div_y, _RW, 10)
        )
        _cur_preset_names = self._current_preset_names()
        if self._use_random_seed:
            seed_lbl = self.app.t("menu.seed_random")
        elif (self._selected_preset is not None
              and self._selected_preset < len(_cur_preset_names)):
            seed_lbl = self.app.t(
                "menu.seed_named",
                name=_cur_preset_names[self._selected_preset],
                seed=self.seed,
            )
        else:
            seed_lbl = self.app.t("menu.seed_number", seed=self.seed)
        _draw_label(surface, seed_lbl, _RX, map_label_y, max_w=_RW)

        # Divider before Run
        run_div_y = (
            self._practice_run_div_y()
            if self.launch_mode == "practice"
            else self._classroom_run_div_y()
        )
        skin.draw_ornamental_divider(
            surface, pygame.Rect(_RX, run_div_y, _RW, 10)
        )

        # Widgets (drawn before tile row so tiles render on top)
        self._widgets.draw(surface)

        self._draw_mode_tabs(surface)

        if self.launch_mode == "practice":
            self._draw_opponent_cards(surface)

        if self._show_boss_difficulty():
            self._draw_difficulty_cards(surface)

        # Tile row (drawn on top of widget hit-areas)
        self._draw_tile_row(surface, self._tiles_y)

        # Error
        if self.error:
            skin.draw_text_clipped(
                surface, self.error,
                pygame.Rect(_RX, error_y, _RW, 22),
                body_font(13), colors.RED_FAIL, align="left",
            )

    # ── Sub-drawing helpers ───────────────────────────────────────────────────

    def _draw_selectable_card(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        *,
        is_active: bool,
        is_hovered: bool,
    ) -> None:
        skin.draw_panel(surface, rect, style="parchment" if is_active else "stone")

        if is_active:
            bar = pygame.Rect(rect.x, rect.y, 4, rect.height)
            pygame.draw.rect(surface, colors.TEAL_ACCENT, bar, border_radius=2)
            pygame.draw.rect(surface, colors.TEAL_ACCENT, rect, 2, border_radius=6)
        elif is_hovered:
            ov = pygame.Surface(rect.size, pygame.SRCALPHA)
            ov.fill((255, 220, 120, 28))
            surface.blit(ov, rect.topleft)
            pygame.draw.rect(surface, colors.STONE_HIGHLIGHT, rect, 1, border_radius=6)
        else:
            ov = pygame.Surface(rect.size, pygame.SRCALPHA)
            ov.fill((0, 0, 0, 40))
            surface.blit(ov, rect.topleft)

    def _draw_selected_badge(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
    ) -> None:
        badge_font = body_font(10)
        badge = badge_font.render(self.app.t("menu.selected"), True, colors.TEAL_ACCENT)
        surface.blit(badge, (rect.right - badge.get_width() - 8, rect.y + 6))

    def _draw_mode_tabs(self, surface: pygame.Surface) -> None:
        tabs: list[tuple[LaunchMode, Button, str, str]] = [
            ("practice", self._prac_tab, self.app.t("menu.practice_tab"), "shield"),
            ("classroom", self._class_tab, self.app.t("menu.classroom_tab"), "classroom"),
        ]
        icon_size = 18
        font = body_font(15)

        for mode, btn, label, icon in tabs:
            rect = btn.rect
            is_active = self.launch_mode == mode
            is_hovered = btn.hovered and btn.enabled and not is_active
            self._draw_selectable_card(
                surface, rect, is_active=is_active, is_hovered=is_hovered
            )

            text_color = colors.PARCHMENT_TEXT if is_active else (
                colors.GOLD_TEXT if is_hovered else colors.TEXT_MUTED
            )
            text_surf = font.render(label, True, text_color)
            gap = 6
            content_w = icon_size + gap + text_surf.get_width()
            content_x = rect.x + (rect.width - content_w) // 2
            text_y = rect.y + (rect.height - text_surf.get_height()) // 2

            icon_rect = pygame.Rect(content_x, rect.y, icon_size, rect.height)
            draw_menu_icon(surface, icon, icon_rect, text_color)
            surface.blit(text_surf, (content_x + icon_size + gap, text_y))

            if is_active:
                self._draw_selected_badge(surface, rect)

    def _opponent_button(self, mode: str) -> Button | None:
        for opp_mode, btn in self._opponent_buttons:
            if opp_mode == mode:
                return btn
        return None

    def _draw_opponent_cards(self, surface: pygame.Surface) -> None:
        sid = (
            self.scenarios[self.selected].get("id", "resource_wars")
            if self.scenarios else "resource_wars"
        )
        for mode, card_rect in self._opponent_cards:
            is_active = mode == self.opponent_mode
            btn = self._opponent_button(mode)
            is_hovered = bool(btn and btn.hovered and btn.enabled and not is_active)

            self._draw_selectable_card(
                surface, card_rect, is_active=is_active, is_hovered=is_hovered
            )

            icon_path = builtin_icon_path(mode)
            icon_surf = load_icon(icon_path, size=32) if icon_path else None
            tx = card_rect.x + 12
            if icon_surf:
                surface.blit(icon_surf,
                              (tx, card_rect.y + (card_rect.height - 32) // 2))
                tx += 40

            tc = colors.PARCHMENT_TEXT if is_active else (
                colors.GOLD_TEXT if is_hovered else colors.TEXT_MUTED
            )
            name = self.app.t(f"menu.opponent.{mode}")
            ns = body_font(15).render(name, True, tc)
            surface.blit(ns, (tx, card_rect.y + 6))

            desc_key = (
                f"menu.opponent_desc.{sid}.{mode}"
                if sid in ("resource_wars", "boss_fight", "energy_stations")
                else f"menu.opponent_desc.resource_wars.{mode}"
            )
            desc_color = _PARCH_TYPE if is_active else colors.TEXT_MUTED
            desc_font = body_font(12)
            max_desc_w = card_rect.right - tx - 4
            desc_lines = _wrap_words(self.app.t(desc_key), desc_font, max_desc_w)[:2]
            dy = card_rect.y + 6 + ns.get_height() + 2
            line_step = desc_font.get_height() + 1
            desc_clip = pygame.Rect(tx, dy, max_desc_w, card_rect.bottom - dy - 4)
            old = surface.get_clip()
            surface.set_clip(desc_clip)
            for i, line in enumerate(desc_lines):
                ds = desc_font.render(line, True, desc_color)
                surface.blit(ds, (tx, dy + i * line_step))
            surface.set_clip(old)

            if is_active:
                self._draw_selected_badge(surface, card_rect)

    def _difficulty_button(self, level: int) -> Button | None:
        for diff_level, btn in self._difficulty_buttons:
            if diff_level == level:
                return btn
        return None

    def _draw_difficulty_cards(self, surface: pygame.Surface) -> None:
        for level, card_rect in self._difficulty_cards:
            is_active = level == self.boss_difficulty
            btn = self._difficulty_button(level)
            is_hovered = bool(btn and btn.hovered and btn.enabled and not is_active)

            self._draw_selectable_card(
                surface, card_rect, is_active=is_active, is_hovered=is_hovered
            )

            tx = card_rect.x + 10
            tc = colors.PARCHMENT_TEXT if is_active else (
                colors.GOLD_TEXT if is_hovered else colors.TEXT_MUTED
            )
            ns = body_font(14).render(self.app.t(f"menu.difficulty.{level}"), True, tc)
            surface.blit(ns, (tx, card_rect.y + 8))

            desc_color = _PARCH_TYPE if is_active else colors.TEXT_MUTED
            ds = body_font(11).render(self.app.t(f"menu.difficulty.{level}.desc"), True, desc_color)
            dy = card_rect.y + 8 + ns.get_height() + 2
            old = surface.get_clip()
            surface.set_clip(pygame.Rect(tx, dy, card_rect.right - tx - 4, 28))
            surface.blit(ds, (tx, dy))
            surface.set_clip(old)

            if is_active:
                self._draw_selected_badge(surface, card_rect)

    def _current_preset_names(self) -> list[str]:
        """Return localized preset names for the currently selected scenario."""
        from engine.i18n import map_preset_name

        sid = (
            self.scenarios[self.selected].get("id", "resource_wars")
            if self.scenarios else "resource_wars"
        )
        lang = self.app.lang()
        count = len(self._scenario_preset_names.get(sid, self._preset_names))
        return [map_preset_name(sid, i, lang) for i in range(count)]

    def _draw_tile_row(self, surface: pygame.Surface, row_y: int) -> None:
        """Draw the 6 tiles: col 0 = Random die, cols 1-5 = map presets."""
        label_font = body_font(11)
        preset_names = self._current_preset_names()

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
                label = self.app.t("menu.random")
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
                label = (preset_names[preset_i]
                         if preset_i < len(preset_names) else "")

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
