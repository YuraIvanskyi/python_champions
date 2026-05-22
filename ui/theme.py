"""UI layout constants and config application."""

from __future__ import annotations

from pathlib import Path

from engine.core.config import UIConfig
from ui.skin import assets as skin_assets
from ui.skin import colors
from ui.skin.typography import set_code_font_path, set_game_font_path

# Layout (mutable via apply_config)
TILE_SIZE = 40
MAP_PADDING = 24
MAP_TOP = 16

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 800

MARGIN_X = 48
FOOTER_HEIGHT = 24
TOOLBAR_HEIGHT = 44
HUD_TEXT_HEIGHT = 120
HUD_GAP = 8

LABEL_FONT_PT = 14
HUD_TITLE_PT = 24
HUD_BODY_PT = 18
HUD_LINE_SPACING = 24
CENTER_TITLE_PT = 28
CENTER_SUBTITLE_PT = 16
FOOTER_PT = 15
MENU_HINT_PT = 15

HUD_HEIGHT = HUD_TEXT_HEIGHT + TOOLBAR_HEIGHT + HUD_GAP

# Colors from RPG skin (backward-compatible names)
COLOR_BG = colors.COLOR_BG
COLOR_PANEL = colors.COLOR_PANEL
COLOR_TEXT = colors.COLOR_TEXT
COLOR_MUTED = colors.COLOR_MUTED
COLOR_ACCENT = colors.COLOR_ACCENT

COLOR_TILE_EMPTY = (48, 52, 62)
COLOR_TILE_RESOURCE = (72, 168, 96)
COLOR_TILE_OBSTACLE = (92, 72, 56)

COLOR_ENTITY_STUDENT = (80, 140, 255)
COLOR_ENTITY_OPPONENT = (240, 96, 96)

COLOR_ENTITY_ALT: tuple[tuple[int, int, int], ...] = (
    (255, 200, 100),
    (200, 120, 255),
    (120, 220, 200),
    (255, 140, 200),
    (200, 200, 120),
)

MIN_HIT_SIZE = 32

TILE_COLORS = {
    "empty": COLOR_TILE_EMPTY,
    "resource": COLOR_TILE_RESOURCE,
    "obstacle": COLOR_TILE_OBSTACLE,
}

_coach_max_quest = 12
_coach_code_font_pt = 14


def coach_config() -> tuple[int, int]:
    return _coach_max_quest, _coach_code_font_pt


def apply_config(ui: UIConfig) -> None:
    """Update module-level layout / typography from TOML (call before pygame.set_mode)."""
    global TILE_SIZE, MAP_PADDING, MAP_TOP
    global WINDOW_WIDTH, WINDOW_HEIGHT, MARGIN_X
    global HUD_TEXT_HEIGHT, LABEL_FONT_PT, HUD_TITLE_PT, HUD_BODY_PT, HUD_LINE_SPACING
    global CENTER_TITLE_PT, CENTER_SUBTITLE_PT, FOOTER_PT, MENU_HINT_PT
    global HUD_HEIGHT, _coach_max_quest, _coach_code_font_pt

    TILE_SIZE = ui.tile_size
    MAP_PADDING = ui.map_padding
    MAP_TOP = ui.map_top
    WINDOW_WIDTH = ui.window_width
    WINDOW_HEIGHT = ui.window_height
    MARGIN_X = ui.margin_x
    LABEL_FONT_PT = ui.label_font_pt
    HUD_TITLE_PT = ui.hud_title_pt
    HUD_BODY_PT = ui.hud_body_pt
    HUD_LINE_SPACING = ui.hud_line_spacing
    CENTER_TITLE_PT = ui.center_title_pt
    CENTER_SUBTITLE_PT = ui.center_subtitle_pt
    FOOTER_PT = ui.footer_pt
    MENU_HINT_PT = ui.menu_hint_pt
    HUD_TEXT_HEIGHT = max(100, ui.hud_body_pt * 4 + 36)
    HUD_HEIGHT = HUD_TEXT_HEIGHT + TOOLBAR_HEIGHT + HUD_GAP

    _coach_max_quest = ui.coach.max_quest_cards
    _coach_code_font_pt = ui.coach.code_panel_font_pt

    manifest = Path(ui.theme.asset_manifest)
    skin_assets.configure(
        manifest_path=manifest if manifest.is_file() else Path("ui/assets/manifest.toml"),
        use_sliced=ui.theme.use_sliced_assets,
    )
    set_game_font_path(Path(ui.theme.game_font))
    set_code_font_path(Path(ui.theme.code_font))


def hud_text_top(window_height: int | None = None) -> int:
    h = WINDOW_HEIGHT if window_height is None else window_height
    return (
        h
        - FOOTER_HEIGHT
        - TOOLBAR_HEIGHT
        - HUD_GAP
        - HUD_TEXT_HEIGHT
        - HUD_GAP
    )


def toolbar_top(window_height: int | None = None) -> int:
    h = WINDOW_HEIGHT if window_height is None else window_height
    return h - FOOTER_HEIGHT - TOOLBAR_HEIGHT - HUD_GAP


def footer_top(window_height: int | None = None) -> int:
    h = WINDOW_HEIGHT if window_height is None else window_height
    return h - FOOTER_HEIGHT


def content_width(window_width: int | None = None) -> int:
    w = WINDOW_WIDTH if window_width is None else window_width
    return w - 2 * MARGIN_X
