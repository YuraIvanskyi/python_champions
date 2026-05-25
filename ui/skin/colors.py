"""Named palette — derived from bg.jpg dungeon atmosphere + ui_reference.png RPG kit."""

from __future__ import annotations

# ── Core backgrounds ──────────────────────────────────────────────────────────
# Bg.jpg: deep purple-grey stone walls, warm torchlight
SLATE_DARK  = (28, 30, 40)     # base fill under bg.jpg (almost never visible)
SLATE_PANEL = (44, 50, 66)     # stone panel fill — cool blue-grey brick

# ── Stone panel ───────────────────────────────────────────────────────────────
STONE_BORDER    = (65, 73, 92)    # mortar / panel frame
STONE_HIGHLIGHT = (95, 106, 130)  # chipped-stone top-left bevel
STONE_SHADOW    = (22, 25, 34)    # deep corner shadow

# ── Wood panel (torchlit dungeon door warmth) ─────────────────────────────────
WOOD_LIGHT  = (210, 155, 68)   # warm amber trim / highlight
WOOD_FILL   = (118, 76, 36)    # rich dark wood (matches bg.jpg door)
WOOD_BORDER = (88, 54, 20)     # darkest wood edge
WOOD_GRAIN  = (105, 70, 34)    # subtle grain line

# ── Parchment panel (aged dungeon scroll) ─────────────────────────────────────
PARCHMENT      = (242, 218, 158)   # warm parchment fill
PARCHMENT_EDGE = (192, 165, 108)   # aged edge / fold vignette
PARCHMENT_TEXT = (42, 32, 18)      # very dark brown

# ── Metal accents ─────────────────────────────────────────────────────────────
RIVET        = (160, 168, 192)  # bright iron rivet
RIVET_SHADOW = (85, 92, 110)    # rivet shadow side

# ── Buttons ───────────────────────────────────────────────────────────────────
BUTTON_HOVER   = (74, 92, 118)   # hover fill
BUTTON_PRESSED = (28, 32, 46)    # pressed / active fill

# ── Background vignette ───────────────────────────────────────────────────────
# Warm torch-fire red; used when procedural background is the fallback
VIGNETTE_WARM = (88, 18, 6)

# ── Text ─────────────────────────────────────────────────────────────────────
# Crown/banner gold from bg.jpg torches & ui_reference trim
GOLD_TEXT  = (255, 205, 48)
TEXT_BODY  = (230, 235, 250)     # cool near-white (reads on dark stone)
TEXT_MUTED = (150, 160, 185)     # desaturated mid-blue

# ── Accents (ui_reference.png gem/ribbon palette) ────────────────────────────
# Warm torch-gold — selection borders, active tabs, map picks, coach highlights.
# Slightly deeper than GOLD_TEXT so 2 px borders read without competing with titles.
TEAL_ACCENT    = (232, 178, 48)
PURPLE_ACCENT  = (165, 95, 225)   # arcane purple ribbon
EMERALD_PRAISE = (34, 197, 94)    # fresh emerald — praise / pass ribbon
GREEN_OK       = (58, 228, 128)   # potion green (UI success)
RED_FAIL       = (228, 62, 62)    # alert red

# ── Backward-compatible aliases ───────────────────────────────────────────────
COLOR_BG    = SLATE_DARK
COLOR_PANEL = SLATE_PANEL
COLOR_TEXT  = TEXT_BODY
COLOR_MUTED = TEXT_MUTED
COLOR_ACCENT = TEAL_ACCENT
