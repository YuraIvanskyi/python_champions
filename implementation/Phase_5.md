---
phase_id: phase-5
status: done
depends_on: [phase-4]
source_plan: New scenario — cooperative PvE boss fight
completed_at: "2026-05-25"
---

> **PHASE_STATUS:** `DONE`

# Phase 5 — Boss Fight scenario

## Goal

Add a **cooperative PvE scenario** where all student bots fight together against a single computer-controlled boss on an 8×8 grid. Students write bots that move, attack the boss in melee range, and heal themselves or allies at unlimited range.

## Prerequisites

- Phase 4 complete (full engine, sandbox, analysis, student API, and UI all stable)
- `Action` enum extended with `ATTACK`, `HEAL_SELF`, `HEAL_ALLY` (done in the same commit as this phase's engine work)

## Setup

1. Create `scenarios/boss_fight/` package with `__init__.py`, `game.py`, `scenario.toml`.
2. Create student bot template `student_bots/boss_fight_starter.py`.
3. Register the scenario in `engine/core/scenario_registry.py` (same pattern as `resource_wars`).

## Scenario configuration — `scenarios/boss_fight/scenario.toml`

```toml
[scenario]
id = "boss_fight"
name = "Boss Fight"
map_width = 8
map_height = 8
obstacle_count = 6
max_turns = 200
min_players = 1
max_players = 6

[boss]
# 1 = easy | 2 = medium | 3 = hard
difficulty = 1
hp_per_level = [10, 20, 30]
damage_per_level = [1, 2, 3]
# level 3 hits up to 2 adjacent bots per turn
multi_target_at_level = [false, false, true]

[player]
max_hp = 4
attack_damage = 1
heal_amount = 2

[scoring]
gameplay_weight = 0.7
code_weight = 0.3
```

## Implementation steps

### 1. Extend `engine/core/action.py`

Add three new `Action` members (these are scenario-specific; unsupported scenarios treat them as `WAIT`):

- `ATTACK` — melee; attacks the boss if it occupies an orthogonally adjacent cell; wasted (no energy/turn penalty beyond using the turn) if boss not adjacent.
- `HEAL_SELF` — restores `heal_amount` HP to self, capped at `max_hp`.
- `HEAL_ALLY` — restores `heal_amount` HP to the living ally with the lowest current HP (auto-targeted, unlimited range); heals self if no other living ally exists.

### 2. HP model (`scenarios/boss_fight/game.py`)

- Every bot and the boss carry `current_hp` / `max_hp` tracked inside the scenario (not in the core `Player` dataclass; use a dict keyed by `player_id` plus a `"boss"` entry).
- A bot reaching 0 HP is marked `dead`; dead bots are skipped on subsequent turns (their `make_turn` is not called).
- Boss reaching 0 HP → `is_finished()` returns `True`; all surviving bots win.

### 3. Map setup (`setup()`)

- Place `obstacle_count` obstacles on random interior cells (seeded RNG, same pattern as `resource_wars`).
- Boss spawns at the grid centre `(width // 2, height // 2)`.
- Bots are spread around the outer ring of the map, evenly spaced (seeded order).

### 4. Turn resolution order (`apply_turn()`)

1. Apply student bot actions in sorted `player_id` order (dead bots skipped).
2. Apply boss AI action last.

Resolve movement with the same `_can_move_to()` logic as `resource_wars` (blocked by obstacles and occupied cells).

### 5. Boss AI levels

| Level | Movement | Attack |
|-------|----------|--------|
| 1 easy | Move one step toward nearest living bot (Manhattan distance); attack one adjacent bot for `damage_per_level[0]` | Single target |
| 2 medium | Move toward nearest; if two or more bots adjacent, attack the one with lowest HP | Single target, smart targeting |
| 3 hard | Move toward centre-of-mass of all living bots; attack up to 2 adjacent bots per turn (lowest HP first) | Multi-target |

Boss movement is blocked by obstacles; it can enter cells occupied by bots (boss does not push, it attacks).

### 6. Combat resolution

- **Bot ATTACK:** bot deals `attack_damage` to boss if boss is orthogonally adjacent; otherwise turn is wasted.
- **Bot HEAL_SELF:** bot's `current_hp` increases by `heal_amount`, capped at `max_hp`.
- **Bot HEAL_ALLY:** find living ally with minimum `current_hp`; increase that ally's HP by `heal_amount` capped at `max_hp`.
- **Boss attack:** boss deals `damage_per_level[difficulty-1]` to target bot(s); bot HP reduced; at 0 → dead.

### 7. `build_game_state()` additions

The scenario returns an extended dict for the student API:

```python
{
    # existing keys (position, turn, map, others, …)
    "my_hp": int,
    "my_max_hp": int,
    "boss_position": {"x": int, "y": int},
    "boss_hp": int,
    "boss_max_hp": int,
    "boss_difficulty": int,
    "others_hp": {
        "<player_id>": {"hp": int, "max_hp": int, "alive": bool},
        …
    },
}
```

### 8. `BossFightView(GameView)` in `engine/student_api/`

Extend `GameView` with a subclass `BossFightView` that adds:

| Method | Returns | Description |
|--------|---------|-------------|
| `my_hp()` | `int` | Current bot HP |
| `my_max_hp()` | `int` | Max bot HP |
| `is_alive()` | `bool` | Whether this bot is still alive |
| `boss_x()` | `int` | Boss column |
| `boss_y()` | `int` | Boss row |
| `boss_hp()` | `int` | Current boss HP |
| `boss_max_hp()` | `int` | Max boss HP |
| `is_boss_adjacent()` | `bool` | Boss is orthogonally adjacent to this bot |
| `ally_hp(player_id)` | `int \| None` | HP of a named ally |
| `weakest_ally_id()` | `str \| None` | player_id of living ally with lowest HP |

The scenario passes a `BossFightView` instance to each bot's `make_turn`.

### 9. Victory and scoring

- **Win:** boss HP ≤ 0 → `gameplay_score` for each surviving bot proportional to damage it personally dealt, normalised to 0–100.
- **Loss / timeout:** all bots dead or `max_turns` reached → partial score by total damage dealt (more damage = higher score, capped at ~80 to distinguish win).
- `final_score = gameplay_score * 0.7 + code_quality * 0.3`
- `metrics.json` additions: `boss_hp_final`, `damage_dealt` (per bot), `heals_given`, `heals_received`, `turns_alive`.

### 10. Student bot template: `student_bots/boss_fight_starter.py`

```python
"""Boss Fight starter bot.

Available actions: MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, ATTACK, HEAL_SELF, HEAL_ALLY, WAIT

state methods: my_hp(), my_max_hp(), boss_x(), boss_y(), boss_hp(),
               is_boss_adjacent(), ally_hp(player_id), weakest_ally_id()
"""


def make_turn(state):
    # heal if low on health
    if state.my_hp() < 2:
        return "HEAL_SELF"
    # attack boss if adjacent
    if state.is_boss_adjacent():
        return "ATTACK"
    # move toward boss
    bx, by = state.boss_x(), state.boss_y()
    if bx > state.my_x():
        return "MOVE_RIGHT"
    if bx < state.my_x():
        return "MOVE_LEFT"
    if by > state.my_y():
        return "MOVE_DOWN"
    return "MOVE_UP"
```

### 11. UI integration

- Register `boss_fight` in the scenario picker (menu + launcher).
- Render the boss as a **distinct oversized tile** (e.g., 1.5× tile size or a unique sprite) at its grid position.
- Draw **HP bars** beneath each bot and the boss (coloured bar, width proportional to `current_hp / max_hp`).
- Show "BOSS DEFEATED" / "PARTY WIPED" end-screen text.
- Replay viewer: playback works with existing turn-by-turn system; HP state stored per turn in `replay.json`.

### 12. Tests

- `tests/test_boss_fight_setup.py` — boss spawns at centre, bots at edges, HP initialised from config
- `tests/test_boss_fight_combat.py` — `ATTACK` reduces boss HP by `attack_damage`; `HEAL_SELF` restores HP (capped); `HEAL_ALLY` targets weakest ally
- `tests/test_boss_fight_ai.py` — level 1 boss moves toward nearest bot; level 2 targets lowest-HP adjacent bot; level 3 attacks up to 2
- `tests/test_boss_fight_win_lose.py` — boss at 0 HP → `is_finished()` True, scores set; all bots dead → `is_finished()` True
- `tests/test_boss_fight_regression.py` — identical seed + bots → identical `replay.json`

## Out of scope

- Multiplayer boss modes (different bosses for each team)
- Boss loot or power-ups
- Tournament integration (Phase 5 is scenario-only; tournament is deferred)

## Definition of done

- [x] `code-scenarios run --scenario boss_fight --bots student_bots/boss_fight_starter.py --seed 1` completes headless
- [x] `difficulty` 1, 2, and 3 all run without error; level 3 boss attacks up to 2 targets per turn
- [x] `ATTACK`, `HEAL_SELF`, `HEAL_ALLY` all produce correct HP changes in tests
- [x] Dead bots are skipped each turn; scenario ends immediately when all bots are dead
- [x] Boss win recorded with correct per-bot `damage_dealt` in `metrics.json`
- [x] `BossFightView` methods accessible from starter bot; documented in template comments
- [x] UI shows boss as distinct tile with HP bar; bot HP bars visible during simulation
- [x] All Phase 5 tests pass

## Verification

```bash
pytest tests/test_boss_fight_setup.py tests/test_boss_fight_combat.py tests/test_boss_fight_ai.py tests/test_boss_fight_win_lose.py tests/test_boss_fight_regression.py -v
code-scenarios run --scenario boss_fight --bots student_bots/boss_fight_starter.py --seed 1
code-scenarios run --scenario boss_fight --bots student_bots/boss_fight_starter.py --seed 1
# verify replay.json is identical both runs
python -m ui
# Manual: launch boss_fight from menu, confirm HP bars and boss tile render
```

## References

- [`engine/core/action.py`](../engine/core/action.py) — `ATTACK`, `HEAL_SELF`, `HEAL_ALLY` additions
- [`engine/student_api/`](../engine/student_api/) — `BossFightView` subclass
- [`scenarios/resource_wars/game.py`](../scenarios/resource_wars/game.py) — reference for `ScenarioBase` implementation pattern
- [`engine/core/scenario.py`](../engine/core/scenario.py) — `ScenarioBase` contract
