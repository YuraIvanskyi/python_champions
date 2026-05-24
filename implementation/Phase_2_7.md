---
phase_id: phase-2-7
status: done
depends_on: [phase-2-6]
source_plan: PLAN.md §11 (UI), §12 (data flow), §17 (student API); classroom showcase (not in PLAN verbatim)
---

> **PHASE_STATUS:** `DONE`

# Phase 2.7 — Classroom battle: many student bots + projector-friendly UI

## Goal

Today the engine, CLI, GUI, Resource Wars scenario, replay writer, and `GameView` helpers assume **exactly one sandboxed student** competing against **one built-in AI** on a fixed two-entity map (`student` / `opponent`).

This phase delivers **one shared match** where **multiple student bot files** run on the **same scenario instance** (same seed, same map, same resources), each turn collecting an action per competitor. That supports a classroom or club session: every submitted `.py` bot is visible on the projector at once.

Separately, raise default **tile size**, **window size**, and **HUD / label typography** so the Pygame view reads clearly on a wall projector.

**End-user story:** *"I drop eight student bots into a folder, launch the GUI (or CLI), and everyone watches one big map where all eight agents move and gather — scores and names are readable from the back row."*

**Non-goals (defer):**

- **Phase 5 tournament mode** remains *batch of isolated matches* and rankings. Phase 2.7 is *one simultaneous multi-agent game*, not a round-robin league table.
- **Phase 6** teams, fog, and comms APIs stay out of scope unless trivially compatible; do not block 2.7 on those designs.

## Prerequisites

- Phase 2.6 done (`GameView`, loader wrapping, tests green).
- Comfortable extending Resource Wars and breaking internal assumptions where needed, while keeping **determinism** (same seed + same bot set + same order → same `replay.json`).

## Relationship to existing code (audit hints)

| Area | Current limitation |
| --- | --- |
| `engine/core/live_game.py` | One `student_bot`, one `SandboxedBot`, hard-coded `student` / `opponent` action keys and `build_render_state` entity list |
| `scenarios/resource_wars/game.py` | Two fixed entities and scores; `build_game_state` exposes a single `opponent_position` |
| `engine/core/cli.py` | `--bot` single path only |
| `ui/screens/menu.py` | Single bot path field |
| `engine/core/session.py` | `replay["bot"]` single string |
| `engine/student_api/view.py` | `opponent_*` assumes one rival |
| `ui/theme.py` / `ui/render/map_renderer.py` | `TILE_SIZE = 32`, small label font (e.g. 11 px) |

## Setup

1. Read this phase fully; skim `resource_wars/game.py`, `live_game.py`, `menu.py`, `simulation.py`, `write_session`.
2. Decide **maximum competitors** for Resource Wars (recommend **2–8**, configurable in `scenarios/resource_wars/scenario.toml` or `configs/default.toml`) so spawn placement and UI stay bounded.

## Implementation steps

### 1. Scenario: N-player Resource Wars (engine rules)

- Replace the fixed `"student"` / `"opponent"` pair with a **dynamic player id set** established at `setup()` time (e.g. `player_ids: list[str]` passed from `LiveGame`, or derived from bot stems with collision-safe suffixes).
- **Spawn layout:** deterministic from `seed` + ordered player list (e.g. distribute along perimeter or fixed corner slots documented in `scenario.toml`). No overlap with obstacles; validate count vs map size.
- **`_scores` / `_entities`:** keyed by each player id.
- **`apply_turn`:** unchanged semantics per player; iteration order over `actions` should be **stable** (sorted player id) so tie-breaking and event ordering are reproducible.
- **`build_game_state(viewer_id)`:** include full readonly map as today; replace lone `opponent_position` with structured rivals data, for example:
  - `others: dict[str, [x, y]]` mapping **other** player id → position, or
  - `units: list[{"id", "x", "y"}]` excluding the viewer.
- **`is_finished` / victory:** any player may hit `score_threshold`; document behavior when multiple reach threshold same turn (both win vs earliest in stable order — pick one and test it).

Keep a **compatibility path** if useful for tests: a two-player configuration that matches current replay shape *or* explicitly version replay (`"schema_version"` field) if the JSON shape changes materially.

### 2. Opponent AI policy for multi-student matches

Pick one policy and document it in the phase banner / `scenario.toml`:

- **Option A (recommended for classroom):** match is **students only** — no built-in greedy/dumb AI. If only one bot is loaded, either refuse with a clear error or auto-append one dumb AI (team choice: prefer **clear error** unless product wants practice mode).
- **Option B:** optional `--opponent greedy` adds **one** extra AI-controlled entity (total N+1). Only if time permits; not required for “all students compete” story.

Default menu/CLI for **multi-bot** should not silently mix in AI unless the user selects it.

### 3. Loader and player identity

- Extend `load_bot` usage: for each file path, assign `player_id` (stable string), `display_name` / icon from existing profile metadata (`BOT_NAME`, icon path).
- Ensure **unique** `player_id` when two files share the same stem (hash suffix or index).

### 4. `LiveGame` and `run_game`

- API sketch: `student_bots: list[Bot]` (or `bots: list[Bot]` with `is_student` flags) instead of a single `student_bot`.
- **Sandboxes:** one `SandboxedBot` session **per distinct source path**; if duplicate paths, reuse one session or reject duplicates at CLI/UI.
- **Per turn:** for each student path, `build_game_state(that_id)` → sandbox `make_turn` → collect `Action`. Non-student AI (if any) uses existing `resolve_ai_turn` with appropriate viewer id.
- **Logging / status:** generalize `text_log` lines to list all `player_id=action` pairs; timeout messages should name the bot file or display name.
- **`build_render_state`:** build `entities` from **all** units with `display_name` / `icon` from `Player` profiles; remove the hard-coded `("student", "position"), ("opponent", "opponent_position")` tuple.

### 5. `GameView` (student API)

- Parse new rivals structure from the dict IPC payload.
- Add methods such as `other_units()`, `position_of(player_id: str)`, or `others_positions() -> list[tuple[str, int, int]]`.
- Preserve existing **`opponent_x` / `opponent_y`** when the scenario exposes exactly **one** other human-readable rival (two-player mode), **or** define that they refer to “first other in sorted id order” only for backward tests — prefer explicit two-player replay tests vs ambiguous semantics.

### 6. CLI

- Add **`--bots`** accepting **multiple** paths (`nargs="+"`) **or** repeatable `--bot` flags — pick one style and document in `--help`.
- Optional: **`--bots-dir`** loading all `*.py` in a directory (sorted by name for determinism), with a `--max-bots` cap.
- Keep existing **`--bot` single file** working for current two-player (one student + AI) flows.
- Validation: player count within scenario limits; friendly errors.

### 7. Pygame UI

- **Menu:** support entering multiple paths (multi-line field, comma-separated list, or “Add bot” rows) and/or “Choose folder” for `--bots-dir`-equivalent. Show count and truncation if over max.
- **`App.start_simulation` / `SimulationScreen`:** accept a list of `Bot` + paths; pass into `LiveGame`.
- **Scores / replay screens:** handle `final_scores` dict with **N keys**; ensure layout wraps or scrolls.

### 8. Replay and results (`write_session`)

- Replace or extend `replay["bot"]` with something like `replay["bots"]: [paths...]` or `replay["players"]: { id: { "bot": path?, "display_name": ... } }`.
- If old key is kept for backward compatibility, document deprecation; update replay loader in UI if it assumes a single `"bot"` string.

### 9. Tests

- **Scenario:** multi-player spawn, collision blocking between three+ units, gather scoring per id, deterministic `apply_turn` event order.
- **`LiveGame`:** mock sandbox or small real bots; assert each bot receives state with correct `player_id` and others’ positions.
- **CLI / integration smoke:** `code-scenarios run ...` with two real files from `student_bots/` (e.g. duplicate `example_bot.py` under two names if needed).
- **Optional:** UI smoke test remains display-skippable per existing project patterns.

### 10. Projector-friendly visuals

- Increase **`TILE_SIZE`** and **`WINDOW_WIDTH` / `WINDOW_HEIGHT`** defaults in `ui/theme.py` (or drive from **`configs/default.toml`** under a new `[ui]` table: `tile_size`, `window_width`, `window_height`, `label_font_pt`, `hud_font_pt`) so one place adjusts “showcase” sizing.
- **Map renderer:** scale **entity icons**, **circle fallback**, and **name labels** with tile size (avoid fixed 11 px on large tiles).
- **HUD / toolbar / menu:** bump base font sizes proportionally; ensure `MIN_HIT_SIZE` still meets touch targets if used.
- **Layout:** verify vertical stack (map + HUD + toolbar + footer) fits **without clipping** for default Resource Wars map dimensions at the new sizes; if not, reduce map padding or allow **resizable window** / **scroll** as a stretch goal.

### 11. Registry and docs

- Register `phase-2-7` in `implementation/PHASE_REGISTRY.yaml` and the phase index in `implementation/README.md`.
- Add row to phase table in `AGENTS.md`.

## Verification

```bash
ruff check .
pytest -v
# Single-bot backward compatibility
code-scenarios run --scenario resource_wars --bot student_bots/example_bot.py --seed 42
# Multi-bot (exact command TBD during implementation)
code-scenarios run --scenario resource_wars --bots student_bots/example_bot.py student_bots/example_bot.py --seed 42
code-scenarios gui
```

Adjust the `--bots` example if the implementation chooses a different flag shape.

Manual: launch GUI on a large display or projector; confirm tiles, entity markers, and score text are readable from ~3 meters.

## Definition of done

- [x] Resource Wars (or documented successor scenario id) supports **N ≥ 2** simultaneous student-controlled agents on one map with deterministic outcomes.
- [x] `LiveGame` / `run_game` run one match collecting **per-bot** sandboxed turns (or equivalent safe execution).
- [x] CLI supports **multiple bot paths** without breaking single `--bot` use case.
- [x] GUI can start a match with **multiple bots** and render **all** entities with names/icons.
- [x] `GameView` exposes multi-opponent information; student `example_bot` or docs updated for N-player awareness.
- [x] `replay.json` records **all** bot paths / player metadata needed to replay faithfully.
- [x] Default UI **tile and window sizes** and **fonts** are increased for projector readability; no major clipping on default map.
- [x] `pytest` passes; phase registry + README + `AGENTS.md` synced when marking **done**.
