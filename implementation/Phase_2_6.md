---
phase_id: phase-2-6
status: done
depends_on: [phase-2-5]
source_plan: PLAN.md §17 (bot API / game state)
---

> **PHASE_STATUS:** `DONE`

# Phase 2.6 — Simpler student bot API

## Goal

Replace confusing **dict key** access (`game_state["position"]`, `game_state.get("on_resource")`) with a **readonly `GameView`** object that exposes simple methods: `state.my_x()`, `state.on_resource()`, `state.is_walkable(x, y)`, and so on.

Students should not need to remember JSON field names or worry about mutating shared state. The engine still serializes dicts into the sandbox subprocess; wrapping happens at the loader boundary.

**End-user story:** *"I write `if state.on_resource(): return 'GATHER'` and use `state.is_walkable(nx, ny)` — I never touch brackets on a mystery dict."*

## Prerequisites

- Phase 2.5 complete (GUI polish, bot identity)
- `build_game_state()` in Resource Wars unchanged in shape (dict for IPC)

## Setup

1. Confirm Phase 2.5 verification passes.
2. Add package `engine/student_api/` with `GameView` and `TileKind` constants.

## Implementation steps

### 1. `GameView` readonly facade (`engine/student_api/view.py`)

Methods (Resource Wars baseline):

| Method | Replaces dict access |
| --- | --- |
| `turn()`, `player_id()` | `turn`, `player_id` |
| `my_x()`, `my_y()`, `position()` | `position` |
| `score()` | `resources` |
| `on_resource()` | `on_resource` |
| `map_width()`, `map_height()` | `map_width`, `map_height` |
| `opponent_x()`, `opponent_y()`, `opponent_position()` | `opponent_position` |
| `is_inside(x, y)` | bounds checks |
| `tile_at(x, y)` | scan `visible_tiles` |
| `is_walkable(x, y)`, `is_obstacle(x, y)` | tile helpers |
| `has_resource_at(x, y)`, `resource_tiles()` | resource helpers |
| `manhattan_to_nearest_resource(x, y)` | common greedy pattern |

`TileKind.EMPTY`, `RESOURCE`, `OBSTACLE` — string constants for comparisons.

No `__getitem__` / `__setitem__` on `GameView` (not dict-like).

### 2. Wire through loader and `BotBase`

- `_wrap_make_turn`: `GameView.from_dict(game_state)` before calling student code
- `BotBase.make_turn(self, state: GameView)` type hint
- Built-in AIs (`simple_ai`, `dumb_ai`) keep internal dicts — engine-only

### 3. Update `student_bots/example_bot.py`

Rewrite using `GameView` methods; document API in module docstring (no dict key list).

### 4. Tests

- `tests/test_game_view.py` — unit tests for all helpers
- Update `tests/test_loader.py` — example bot still returns valid actions
- Full `pytest` must pass

### 5. Registry and docs

- Add `phase-2-6` to `PHASE_REGISTRY.yaml` and `implementation/README.md` index
- Update `AGENTS.md` phase table

## Verification

```bash
pytest -v tests/test_game_view.py tests/test_loader.py tests/test_engine_turns.py
pytest -v
code-scenarios run --scenario resource_wars --bot student_bots/example_bot.py --seed 42
```

## Definition of done

- [x] `GameView` in `engine/student_api/` with methods above
- [x] Loader wraps dict → `GameView` for every `make_turn` call
- [x] `example_bot.py` uses method API only
- [x] `tests/test_game_view.py` covers helpers
- [x] `pytest` passes
- [x] Phase registry + banner marked `done`
