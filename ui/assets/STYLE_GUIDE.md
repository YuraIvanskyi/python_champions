# UI style guide (Phase 2.8+)

Medieval fantasy RPG chrome aligned to `implementation/ui_reference.png`.

## Palette

| Name | RGB | Use |
| --- | --- | --- |
| slate_dark | 32, 36, 46 | Window background fallback |
| slate_panel | 48, 54, 66 | Stone panel fill fallback |
| wood_light | 168, 132, 88 | Wood panel accent |
| parchment | 232, 216, 176 | Hint / quest text areas |
| gold_text | 240, 200, 80 | Titles, primary button labels |
| teal_accent | 232, 178, 48 | Selection borders, active tabs, efficiency ribbon |
| purple_accent | 140, 100, 200 | Logic / warning category |
| green_ok | 80, 200, 120 | Confirm, praise |
| red_fail | 220, 80, 80 | Cancel, critical |

## Asset naming

- `chrome.*` — nine-slice panels and buttons (`ui/assets/chrome/`)
- `icons.*` — bot portraits and map entities (`ui/assets/icons/`)
- `tiles.*` — optional map overlays (`ui/assets/tiles/`)

Manifest: `ui/assets/manifest.toml`. Regenerate slices: `python scripts/slice_ui_assets.py`.

## Layout rules

- Minimum clickable height: **40px** (projector / young users).
- Icon buttons: **48×48** hit target.
- Nine-slice insets: see manifest per asset; do not stretch corners.
- Title font: display face from `[ui.theme] title_font` or bold SysFont fallback.
- Body / code: monospace (Consolas/Courier).

## Screen mapping

| Chrome | Screens |
| --- | --- |
| `bg_main` | Full-window backdrop (menu, scores) |
| `panel_stone` | HUD, toolbars, technical coach cards |
| `panel_wood` | Scenario lists, score boards |
| `panel_parchment` | Hints, coach quests, replay session list |
| `button_primary` | Run match, Play again, Code coach |
| `banner_title` | Screen titles |

## Do / don't

- **Do** keep game rules in `engine/` only; UI reads state and metrics.
- **Do** use procedural fallbacks when a slice PNG is missing (logged once).
- **Don't** add real-time physics or networking in UI phases.
