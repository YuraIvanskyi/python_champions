#!/usr/bin/env python3
"""Slice 100 character portrait icons from implementation/char__icons.png.

The source sheet is a 10×10 grid (1254×1254 px) with:
  - Left/top borders (~21 px / ~28 px)
  - 15 px gaps between cells
  - Each icon cell ~107–108 px

Output: ui/assets/icons/char_000.png … char_099.png (row-major order)
Re-run any time the source sheet is replaced.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "implementation" / "char__icons.png"
OUT_DIR = ROOT / "ui" / "assets" / "icons"

# Exact column boundaries (x_start, x_end) inclusive, derived by scanning
# background-color runs in the source image.
COLS = [
    (21, 127),
    (143, 249),
    (265, 372),
    (388, 494),
    (510, 617),
    (633, 740),
    (756, 863),
    (879, 985),
    (1001, 1108),
    (1124, 1230),
]

# Exact row boundaries (y_start, y_end) inclusive.
ROWS = [
    (28, 137),
    (153, 263),
    (279, 388),
    (405, 514),
    (530, 639),
    (656, 765),
    (782, 890),
    (906, 1014),
    (1030, 1133),
    (1149, 1243),
]

assert len(COLS) == 10 and len(ROWS) == 10, "Grid must be 10×10"


def main() -> int:
    if not SOURCE.is_file():
        print(f"Missing source: {SOURCE}", file=sys.stderr)
        return 1

    try:
        from PIL import Image
    except ImportError:
        print("Install Pillow: pip install pillow", file=sys.stderr)
        return 1

    sheet = Image.open(SOURCE).convert("RGBA")
    sw, sh = sheet.size
    if (sw, sh) != (1254, 1254):
        print(
            f"Warning: expected 1254×1254, got {sw}×{sh}. "
            "Boundaries may be off — re-derive COLS/ROWS if needed.",
            file=sys.stderr,
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    written = 0
    for row_idx, (y1, y2) in enumerate(ROWS):
        for col_idx, (x1, x2) in enumerate(COLS):
            icon_idx = row_idx * 10 + col_idx
            crop = sheet.crop((x1, y1, x2 + 1, y2 + 1))
            out_path = OUT_DIR / f"char_{icon_idx:03d}.png"
            crop.save(out_path)
            written += 1

    print(f"Done: {written} icons -> {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
