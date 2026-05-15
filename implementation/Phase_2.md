---
phase_id: phase-2
status: not_started
depends_on: [phase-1]
source_plan: PLAN.md §16 Phase 2, §11
---

> **PHASE_STATUS:** `NOT_STARTED`

# Phase 2 — Local GUI

## Goal

Add a **Pygame CE** desktop interface: scenario selection, visual map, simulation viewer, score screen, and replay viewer ([PLAN.md §16.2](../PLAN.md#16-development-phases), [§11](../PLAN.md#11-uiux-strategy)).

## Prerequisites

- Phase 1 complete (headless engine + CLI + replay JSON)
- `pygame-ce` installed (from Phase 0)

## Setup

1. Confirm Phase 1 verification commands pass.
2. Create `ui/assets/` for tiles, fonts, or simple colored rectangles (pixel/grid aesthetic per PLAN §11).
3. Decide window resolution and tile size (e.g. 32px tiles, 8×8 map → 256×256 play area + chrome).

## Implementation steps

1. **UI package structure** under `ui/`:
   - `ui/app.py` — main application loop, screen state machine
   - `ui/screens/` — `menu.py`, `simulation.py`, `scores.py`, `replay.py`
   - `ui/render/` — `map_renderer.py`, `hud.py`
   - `ui/__main__.py` — `python -m ui` entry point

2. **Scenario selection screen** ([PLAN.md §11 MVP](../PLAN.md#mvp-interface)):
   - List scenarios discovered from `scenarios/` (name + short description)
   - File picker or dropdown for student bot `.py`
   - Optional seed input; "Run" starts simulation

3. **Wire UI to engine** (no duplicate game logic):
   - UI calls same `Game` / scenario classes as CLI
   - Step mode: advance one turn per keypress; auto mode: timed steps
   - Read config from `configs/default.toml` for `max_turns`, timeouts

4. **Map rendering** ([PLAN.md §11 Visualization](../PLAN.md#visualization-style)):
   - 2D tile grid: empty, resource, obstacle, entities by owner color
   - Simple deterministic animations (e.g. slide or snap per turn — avoid real-time physics)

5. **Simulation viewer**:
   - Show current turn, last actions, live scores
   - Pause / step / run controls
   - On finish, transition to score screen

6. **Score screen**:
   - Gameplay scores per player
   - Link/button to open results folder or view last session id
   - "Play again" returns to menu

7. **Replay viewer**:
   - Load `results/session_*/replay.json`
   - Step through stored turns; render map state per turn
   - File browser or list of recent sessions under `results/`

8. **CLI integration** (optional flag):
   - `code-scenarios gui` launches UI; keep `code-scenarios run` for headless

9. **Error handling in UI**:
   - Sandbox timeout → on-screen message, not crash
   - Invalid bot file → clear error before run starts

10. **Tests**:
    - `tests/test_ui_import.py` — import ui modules (may skip if no display in CI)
    - `tests/test_replay_load.py` — replay JSON loads into replay screen model
    - Document `pytest -m "not display"` if headless CI cannot init pygame

## Out of scope

- Static analysis panels (Phase 3)
- Batch tournament UI (Phase 5)
- AI-generated text in UI (Phase 4)
- Screenshots export (optional nice-to-have; not required for done)

## Definition of done

- [ ] `python -m ui` or `code-scenarios gui` opens scenario selection
- [ ] User can pick scenario + bot file and run full simulation visually
- [ ] Map renders grid, resources, obstacles, and entities correctly
- [ ] Score screen shows end-of-game results
- [ ] Replay viewer loads and steps through an existing `replay.json`
- [ ] UI uses engine from Phase 1 (no forked rules)
- [ ] Step/auto modes work without desyncing state
- [ ] Sandbox errors display user-friendly message in UI

## Verification

```bash
uv run pytest tests/test_ui_import.py tests/test_replay_load.py -v
uv run python -m ui
# Manual: run resource_wars with example_bot, complete game, open replay from results/
uv run code-scenarios gui
```

## References

- [PLAN.md §16 — Phase 2](../PLAN.md#16-development-phases)
- [PLAN.md §11 — UI/UX Strategy](../PLAN.md#11-uiux-strategy)
- [PLAN.md §14 — Replay System](../PLAN.md#14-replay-system)
