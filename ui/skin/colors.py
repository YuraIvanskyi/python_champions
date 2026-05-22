"""Named palette from STYLE_GUIDE.md (Phase 2.8 procedural rework)."""

from __future__ import annotations

# --- Core backgrounds ---
SLATE_DARK = (32, 36, 46)
SLATE_PANEL = (48, 54, 66)

# --- Stone panel ---
STONE_BORDER = (60, 68, 82)
STONE_HIGHLIGHT = (80, 88, 102)   # inner top-left edge highlight
STONE_SHADOW = (28, 32, 40)       # inner bottom-right shadow

# --- Wood panel ---
WOOD_LIGHT = (168, 132, 88)
WOOD_FILL = (112, 84, 52)         # darker wood interior fill
WOOD_BORDER = (88, 60, 36)        # wood frame border
WOOD_GRAIN = (100, 72, 44)        # subtle grain line color

# --- Parchment panel ---
PARCHMENT = (232, 216, 176)
PARCHMENT_EDGE = (196, 178, 138)  # aged parchment border/edge vignette
PARCHMENT_TEXT = (50, 40, 28)     # dark brown text on parchment

# --- Metal accents ---
RIVET = (144, 154, 172)           # corner rivet/bolt color
RIVET_SHADOW = (90, 98, 112)      # rivet shadow side

# --- Buttons ---
BUTTON_HOVER = (68, 84, 108)      # button hover fill
BUTTON_PRESSED = (34, 38, 48)     # button pressed fill

# --- Background ---
VIGNETTE_WARM = (72, 24, 14)      # background radial vignette warm color

# --- Text ---
GOLD_TEXT = (240, 200, 80)
TEXT_BODY = (230, 235, 245)
TEXT_MUTED = (140, 150, 170)

# --- Accents ---
TEAL_ACCENT = (72, 180, 170)
PURPLE_ACCENT = (140, 100, 200)
GREEN_OK = (80, 200, 120)
RED_FAIL = (220, 80, 80)

# --- Backward-compatible aliases for ui.theme imports ---
COLOR_BG = SLATE_DARK
COLOR_PANEL = SLATE_PANEL
COLOR_TEXT = TEXT_BODY
COLOR_MUTED = TEXT_MUTED
COLOR_ACCENT = TEAL_ACCENT
