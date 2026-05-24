---
phase_id: phase-2-5
status: done
depends_on: [phase-2]
source_plan: PLAN.md §11 (UI/UX polish), §17 (bot API extensions)
---

> **PHASE_STATUS:** `DONE`

# Phase 2.5 — Playable polish (mouse UI, bot identity, easy opponent)

## Goal

Turn the Phase 2 GUI from a **developer-style keyboard console** into something students and teachers actually want to click through: obvious buttons, visible character identity on the map, and a **second opponent** that feels beatable on the first try.

This phase is about **delight and clarity**, not new game rules. Learners should recognize *their* bot on the grid, pick options with the mouse, and win a match against a “training dummy” before wrestling the smarter built-in AI from Phase 1.

**End-user story:** *“I open the game, click my scenario, choose my bot file, pick ‘Easy’ opponent, hit Run, and watch **Sparky** (my icon) collect resources while **Rookie** wanders around. I don’t need to memorize keyboard cheats.”*

## Prerequisites

- Phase 2 complete (`python -m ui`, replay viewer, simulation screens)
- Phase 1 opponent wiring still works (`greedy_turn` / `simple_ai.py`)
- `ui/assets/` exists (even if mostly placeholders today)

## Setup

1. Confirm Phase 2 verification commands pass.
2. Add asset folders (committed defaults, overridable per bot):

   ```text
   ui/assets/
     tiles/          # optional; colored rects remain fallback
     icons/          # default student / opponent / dumb bot sprites (e.g. 24×24 PNG)
     fonts/          # optional; SysFont fallback OK
   ```

3. Sketch a minimal widget layer plan: one module for hit-tested controls shared by all screens (`ui/widgets/` or `ui/controls/`).
4. Decide default display names: `"You"` / `"Rival"` until a bot file overrides them.

## Implementation steps

### 1. Shared clickable controls (`ui/widgets/`)

Replace “press Enter / ↑↓” as the **primary** interaction model with mouse-first widgets:

- **Button** — label, rect, hover + pressed states, `on_click` callback
- **List / menu row** — scenario picker as clickable rows with clear selection highlight
- **Stepper** — seed +/- as on-screen buttons (not only ←/→ keys)
- **Text field** (lightweight) — bot path with click-to-focus; optional inline edit before run
- **File pick button** — “Browse…” using the existing tk dialog path from `menu.py`, triggered only by click

**Visual polish (student-facing):**

- Cursor changes to hand over clickable regions
- Disabled buttons grayed out with tooltip-style hint text on screen
- Consistent padding and minimum hit target (~32px) for younger users

**Accessibility:** keep keyboard shortcuts as **secondary** (Enter = activate focused button, Esc = back). Document both in a small “Keyboard” footer, not as the main instructions.

### 2. Screen-by-screen mouse wiring

| Screen | Today (Phase 2) | Target (Phase 2.5) |
| --- | --- | --- |
| Menu | ↑↓ scenario, E edit path, Enter run | Click scenario row, Browse / path field, **Run**, **Replays** buttons |
| Simulation | Space step, A auto, P pause | **Step**, **Play/Pause**, **Auto** toolbar buttons; speed optional |
| Scores | Enter play again, V view folder | **Play again**, **Open results**, **View replay** buttons |
| Replay | ←→ step, list ↑↓ | Click session in list, **Step ◀ ▶**, scrub or **Home/End** buttons |

Centralize event routing: `MOUSEBUTTONDOWN` / `MOUSEMOTION` for hover; widgets consume clicks before screen-specific logic.

### 3. Bot identity — names and icons in student files

Extend the **student bot file contract** (document in `example_bot.py` and starter template):

```python
# Optional presentation (sandbox-safe: strings only, no extra imports required)
BOT_DISPLAY_NAME = "Sparky"
BOT_ICON = "student_bots/assets/sparky.png"  # path relative to repo root or bot file dir
```

**Loader / engine (`engine/core/loader.py`, `Player`, replay):**

- After loading module, read optional `BOT_DISPLAY_NAME` and `BOT_ICON` (constants or simple `get_bot_profile()` function — pick one pattern and document it).
- Validate icon path: must resolve under allowed roots (`student_bots/`, `ui/assets/icons/`, or beside the `.py` file); reject absolute paths outside project.
- Pass `display_name` into `Player`; include `display_name` and `icon` (resolved path or asset key) in **replay JSON** per player so replay viewer matches live run.
- Built-in opponents get fixed profiles from config or scenario metadata (not student-editable).

**UI (`ui/render/map_renderer.py`, HUD):**

- Draw sprite centered on tile when icon loads; fallback to colored circle + first letter of name
- Nameplate under or above entity (truncate long names)
- Score / action HUD uses **display names**, not raw `student` / `opponent` ids

### 4. “Dumb” training opponent

Add `engine/simulation/dumb_ai.py` (name may vary) — intentionally weaker than `greedy_turn`:

- Example behavior: random walk among legal moves, rarely `GATHER` even when on a resource, or bias toward `WAIT`
- Same `Action` API as `simple_ai`; no student imports

**Engine / CLI / UI selection:**

- Opponent mode enum or string: `greedy` (default, Phase 1) vs `dumb` (this phase)
- `configs/default.toml` optional `[game] default_opponent = "greedy"`
- Menu + CLI: opponent dropdown or toggle — **“Rival (smart)”** vs **“Rookie (practice)”** with short descriptions
- Register dumb bot profile: `BOT_DISPLAY_NAME`-style defaults in engine (`"Rookie"`, default icon from `ui/assets/icons/rookie.png`)

Ship `student_bots/example_bot.py` unchanged in logic; add optional `BOT_DISPLAY_NAME` demo. Add `student_bots/rookie_challenge.md` or comment in menu — *not required*; the dumb opponent is engine-side.

### 5. Example content for classrooms

- `student_bots/example_bot.py` — set `BOT_DISPLAY_NAME = "Explorer"` and optional icon path example
- `ui/assets/icons/` — include 2–3 default PNGs (student, rival, rookie) or simple generated placeholders committed to repo
- Menu copy: one-line opponent descriptions so teachers know which to assign first

### 6. Tests

- `tests/test_bot_profile.py` — loader reads `BOT_DISPLAY_NAME` / `BOT_ICON`; invalid icon path → clear `BotLoadError` or fallback
- `tests/test_dumb_ai.py` — dumb opponent returns legal actions; over N turns, average score vs greedy is lower (smoke, seeded)
- `tests/test_ui_widgets.py` — button click rect hit test without display (pure geometry)
- `tests/test_replay_load.py` — extend fixtures with `display_name` / icon fields when present
- Manual display test still documented for full pygame interaction

## Out of scope

- Static analysis / metrics panels (Phase 3)
- Tournament bracket UI (Phase 5)
- Animated sprite sheets, sound effects, or online avatar upload
- Letting student bots load arbitrary image bytes from network paths
- Replacing `greedy_turn` as default for CLI headless runs (dumb is opt-in)
- Custom icons for built-in greedy AI beyond a single default sprite

## Definition of done

- [x] Main menu is fully usable with mouse only (scenario, bot path, seed, run, open replays)
- [x] Simulation and replay screens expose obvious clickable transport controls
- [x] Student bot can set display name and icon via documented module constants
- [x] Map and HUD show names; icons render when valid, with sensible fallback
- [x] Replay JSON and replay viewer show the same names/icons as live play
- [x] “Rookie” (dumb) opponent selectable in UI and works in headless `code-scenarios run` with a flag
- [x] Greedy opponent remains available as “smart” rival; behavior unchanged from Phase 1
- [x] Keyboard shortcuts still work for step/run/back where implemented in Phase 2
- [x] New tests pass; Phase 2 tests still pass

## Verification

```bash
pytest tests/test_bot_profile.py tests/test_dumb_ai.py tests/test_ui_widgets.py tests/test_ui_import.py tests/test_replay_load.py -v
code-scenarios run --scenario resource_wars --bot student_bots/example_bot.py --opponent dumb --seed 42
python -m ui
# Manual: menu — click through without keyboard; run with Rookie; confirm name/icon on map
# Manual: replay — names match live session
code-scenarios gui
```

## References

- [PLAN.md §11 — UI/UX Strategy](../PLAN.md#11-uiux-strategy)
- [PLAN.md §17 — Suggested Internal APIs](../PLAN.md#17-suggested-internal-apis)
- [Phase_2.md](Phase_2.md) — baseline GUI (keyboard-first)
- [Phase_3.md](Phase_3.md) — analysis (can run in parallel after Phase 1)

## Why this phase exists

Phase 2 proved the engine and UI work together. Phase 2.5 is what makes the project feel like a **small game** rather than a test harness — the difference between a club demo that holds attention and one where the teacher apologizes for the controls. It is safe to run **in parallel with Phase 3** (analysis is headless); complete it before Phase 5 if tournament demos should look classroom-ready.
