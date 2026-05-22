---
phase_id: phase-2-8
status: done
depends_on: [phase-2-7]
source_plan: PLAN.md §11; ui_reference.png RPG skin
---

> **PHASE_STATUS:** `DONE`

# Phase 2.8 — Playable RPG UI

## Goal

Reskin the Pygame app with medieval fantasy chrome sliced from [ui_reference.png](ui_reference.png): stone/wood/parchment panels, gold titles, and a committed asset manifest + style guide for future art.

## Prerequisites

- Phase 2.7 done (multi-bot GUI, projector sizing)

## Setup

1. Confirm `implementation/ui_reference.png` exists.
2. Run `python scripts/slice_ui_assets.py` after adjusting rects in `ui/assets/manifest.toml` if needed.

## Implementation steps

1. `ui/assets/manifest.toml` + `scripts/slice_ui_assets.py` → `ui/assets/chrome/*.png`
2. `ui/assets/STYLE_GUIDE.md` palette and naming rules
3. `ui/skin/` — assets loader, nine-patch, chrome, typography, colors
4. Extend `UIConfig` / `configs/default.toml` with `[ui.theme]`
5. Reskin `ui/widgets/controls.py` and all screens + `ui/render/hud.py`
6. Light map frame + portrait frames in map/icons renderers
7. Tests: `test_ui_skin_import.py`, `test_slice_manifest.py`

## Rework (2026-05-22): Procedural-first approach

Sliced PNGs from `ui_reference.png` produced poor results (watermarked sprite sheet,
tightly packed elements). The skin was reworked to be **procedural-first**:

- `ui/skin/assets.py`: `_use_sliced` default changed to `False`; PNGs remain optional
- `ui/skin/colors.py`: extended palette (`WOOD_FILL`, `PARCHMENT_EDGE`, `RIVET`, `BUTTON_HOVER`, etc.)
- `ui/skin/chrome.py`: all draw functions rewritten with multi-layer Pygame primitives:
  - stone panels: fill + bevel borders + corner rivets
  - wood panels: fill + grain lines + wood frame + corner pins
  - parchment panels: cream fill + aged-edge vignette
  - `draw_primary_button`: gold border + hover glow + inset press
  - `draw_banner_title`: stone panel with notch accents
  - `draw_text_clipped()`: new helper — truncates with ellipsis, clips surface
  - `draw_background()`: dark slate + warm radial vignette
- `ui/widgets/controls.py`: per-widget pad constants; all text renders use `draw_text_clipped`
- `ui/render/hud.py`, `quest_card.py`: text clipping via `draw_text_clipped` / `surface.set_clip`
- All 5 screens: text blits clipped to their containing panels

## Definition of done

- [x] All screens use skin chrome (procedural fallback only when slice missing)
- [x] `STYLE_GUIDE.md` + `manifest.toml` committed; slice script reproducible
- [x] Projector defaults in config still work
- [x] Phase 2.8 tests pass
- [x] Registry + README + AGENTS.md synced when done

## Verification

```bash
python scripts/slice_ui_assets.py
python -m pytest tests/test_ui_skin_import.py tests/test_slice_manifest.py -v
python -m ui
```
