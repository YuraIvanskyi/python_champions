"""UI colors and layout constants."""

from __future__ import annotations

TILE_SIZE = 32
MAP_PADDING = 24
MAP_TOP = 16

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 660

MARGIN_X = 48
FOOTER_HEIGHT = 24
TOOLBAR_HEIGHT = 44
HUD_TEXT_HEIGHT = 100
HUD_GAP = 8

# Legacy alias — total bottom chrome (text + toolbar, not footer)
HUD_HEIGHT = HUD_TEXT_HEIGHT + TOOLBAR_HEIGHT + HUD_GAP

COLOR_BG = (24, 28, 36)
COLOR_PANEL = (36, 42, 54)
COLOR_TEXT = (230, 235, 245)
COLOR_MUTED = (140, 150, 170)
COLOR_ACCENT = (90, 180, 255)

COLOR_TILE_EMPTY = (48, 52, 62)
COLOR_TILE_RESOURCE = (72, 168, 96)
COLOR_TILE_OBSTACLE = (92, 72, 56)

COLOR_ENTITY_STUDENT = (80, 140, 255)
COLOR_ENTITY_OPPONENT = (240, 96, 96)

MIN_HIT_SIZE = 32

TILE_COLORS = {
    "empty": COLOR_TILE_EMPTY,
    "resource": COLOR_TILE_RESOURCE,
    "obstacle": COLOR_TILE_OBSTACLE,
}


def hud_text_top(window_height: int = WINDOW_HEIGHT) -> int:
    """Y where the HUD text panel begins (below the map)."""
    return (
        window_height
        - FOOTER_HEIGHT
        - TOOLBAR_HEIGHT
        - HUD_GAP
        - HUD_TEXT_HEIGHT
        - HUD_GAP
    )


def toolbar_top(window_height: int = WINDOW_HEIGHT) -> int:
    """Y where transport / control buttons sit."""
    return window_height - FOOTER_HEIGHT - TOOLBAR_HEIGHT - HUD_GAP


def footer_top(window_height: int = WINDOW_HEIGHT) -> int:
    return window_height - FOOTER_HEIGHT


def content_width(window_width: int = WINDOW_WIDTH) -> int:
    return window_width - 2 * MARGIN_X
