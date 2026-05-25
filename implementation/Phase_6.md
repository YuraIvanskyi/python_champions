---
phase_id: phase-6
status: done
depends_on: [phase-5]
source_plan: New scenario — competitive energy gathering with push
completed_at: "2026-05-25"
---

> **PHASE_STATUS:** `DONE`

# Phase 6 — Energy Stations scenario

## Goal

Add a **competitive PvP scenario** on a large 16×16 grid where players gather energy by standing adjacent to stationary stations that carry limited capacity. Players can push rivals away with `ATTACK`. The bot with the most energy when time runs out (or all stations are depleted) wins.

## Prerequisites

- Phase 5 complete (`ATTACK` already in `Action` enum, `BossFightView` pattern established)
- `TileType.STATION` added to `engine/simulation/map.py`

## Setup

1. Create `scenarios/energy_stations/` package with `__init__.py`, `game.py`, `scenario.toml`.
2. Create student bot template `student_bots/energy_stations_starter.py`.
3. Register the scenario in `engine/core/scenario_registry.py`.
4. Add `STATION = "station"` to `TileType` enum in `engine/simulation/map.py`.

## Scenario configuration — `scenarios/energy_stations/scenario.toml`

```toml
[scenario]
id = "energy_stations"
name = "Energy Stations"
map_width = 16
map_height = 16
station_count = 12
obstacle_count = 20
max_turns = 300
min_players = 2
max_players = 8

[player]
starting_energy = 50
max_energy = 150
move_cost = 1      # energy spent per MOVE action
attack_cost = 3    # energy spent per ATTACK action
gather_rate = 5    # energy gained per GATHER while adjacent to a station

[station]
initial_capacity = 20  # total energy units each station holds before depletion

[scoring]
gameplay_weight = 0.7
code_weight = 0.3
```

## Implementation steps

### 1. New `TileType` (`engine/simulation/map.py`)

Add `STATION = "station"` to the `TileType` StrEnum. Existing `resource_wars` code is unaffected because it only reads `RESOURCE` and `OBSTACLE`.

### 2. Map setup (`setup()`)

- Place `obstacle_count` obstacles on random interior cells (seeded RNG).
- Place `station_count` stations on random empty non-obstacle cells; each station is stored in the `Map` as `TileType.STATION` and tracked in a separate `dict[tuple[int,int], int]` mapping `(x, y) → remaining_capacity`.
- Bots placed randomly on empty (non-obstacle, non-station) cells, with minimum separation to avoid immediate contact (seeded).
- Each bot's `current_energy` initialised to `starting_energy`.

### 3. Action semantics

| Action | Cost | Effect |
|--------|------|--------|
| `MOVE_*` | `move_cost` energy | Standard movement; blocked by obstacles, station tiles, other bots |
| `GATHER` | 0 | Valid only when bot is orthogonally adjacent to a `STATION` tile with `capacity > 0`; adds `gather_rate` to bot energy (capped at `max_energy`); reduces station capacity by `gather_rate`; invalid GATHER is treated as `WAIT` |
| `ATTACK` | `attack_cost` energy | Targets the orthogonally adjacent bot in a chosen direction (see note below); pushes that bot one cell further in the same direction; if destination is blocked (wall / obstacle / station / another bot), push is cancelled but energy is still spent; if no bot is in any adjacent cell the action is treated as `WAIT` (no cost) |
| `WAIT` | 0 | No effect |

**ATTACK direction resolution:** the scenario selects the adjacent bot with the lowest `player_id` (deterministic); in future the action format may be extended to `("ATTACK", direction)` but for Phase 6 the auto-target (nearest or only adjacent bot) is sufficient for the student API.

### 4. Gather from multiple sides

Because `GATHER` fires when the bot is *adjacent* (not *on*) the station, up to 4 bots can gather from the same station simultaneously (one per cardinal side). All `gather_rate` deductions are applied in player_id order; if the station capacity drops to 0 mid-turn, later gathers in the same turn that would exceed capacity are capped (bot receives only remaining capacity, station hits 0).

### 5. Station depletion

When a station's `remaining_capacity` reaches 0:
- The `Map` tile at `(x, y)` is set to `TileType.EMPTY`.
- The entry is removed from the capacity dict.
- If all stations are depleted, `is_finished()` returns `True` immediately.

### 6. Energy clamping

- `current_energy` is always clamped to `[0, max_energy]`.
- A bot with `current_energy == 0` attempting `ATTACK` → action silently becomes `WAIT` (no energy deducted).
- A bot with `current_energy == 0` attempting `MOVE_*` → move is still allowed (cost 0 when at 0, i.e. floor clamp); this keeps bots from being permanently frozen.

### 7. `build_game_state()` additions

```python
{
    # existing keys (position, turn, map with STATION tiles, others, …)
    "my_energy": int,
    "max_energy": int,
    "stations": [{"x": int, "y": int, "capacity": int}, …],         # all remaining stations
    "adjacent_stations": [{"x": int, "y": int, "capacity": int}, …], # subset adjacent to this bot
}
```

### 8. `EnergyStationsView(GameView)` in `engine/student_api/`

Extend `GameView` with a subclass `EnergyStationsView` that adds:

| Method | Returns | Description |
|--------|---------|-------------|
| `my_energy()` | `int` | Current energy |
| `max_energy()` | `int` | Energy cap |
| `stations()` | `list[tuple[int,int,int]]` | All remaining stations as `(x, y, capacity)` |
| `adjacent_stations()` | `list[tuple[int,int,int]]` | Stations the bot can currently gather from |
| `can_gather()` | `bool` | Any adjacent station has `capacity > 0` |
| `nearest_station()` | `tuple[int,int] \| None` | `(x, y)` of closest station by Manhattan distance |

The scenario passes an `EnergyStationsView` instance to each bot's `make_turn`.

### 9. Victory and scoring

- **Primary win condition:** `max_turns` elapsed → player with highest `current_energy` wins.
- **Early win condition:** all stations depleted before `max_turns` → same rule (highest energy).
- `gameplay_score` = `current_energy` at end, normalised 0–100 (max energy among all bots = 100).
- `final_score = gameplay_score * 0.7 + code_quality * 0.3`
- `metrics.json` additions: `energy_final`, `gathers`, `pushes_landed`, `pushes_blocked`, `moves`.

### 10. Student bot template: `student_bots/energy_stations_starter.py`

```python
"""Energy Stations starter bot.

Available actions: MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, GATHER, ATTACK, WAIT

state methods: my_energy(), max_energy(), can_gather(), nearest_station(),
               stations(), adjacent_stations()
"""


def make_turn(state):
    # gather if standing next to a station
    if state.can_gather():
        return "GATHER"
    # move toward the nearest station
    nearest = state.nearest_station()
    if nearest:
        nx, ny = nearest
        if nx > state.my_x():
            return "MOVE_RIGHT"
        if nx < state.my_x():
            return "MOVE_LEFT"
        if ny > state.my_y():
            return "MOVE_DOWN"
        return "MOVE_UP"
    return "WAIT"
```

### 11. UI integration

- Register `energy_stations` in the scenario picker.
- Render `STATION` tiles with a **distinct icon** (e.g., lightning bolt or battery sprite).
- Show each station's remaining capacity as a small numeric overlay or shrinking bar on the tile.
- Show each bot's `current_energy` as an energy bar (colour different from the HP bar used in boss_fight).
- On station depletion the tile fades/disappears.
- Replay viewer stores `energy` and `station_capacities` per turn in `replay.json`.

### 12. Tests

- `tests/test_energy_stations_setup.py` — stations placed with correct initial capacity; bots on valid empty cells
- `tests/test_energy_stations_gather.py` — adjacent GATHER increases bot energy by `gather_rate` and reduces station capacity; non-adjacent GATHER is a no-op
- `tests/test_energy_stations_multiside.py` — 4 bots gather from the same station simultaneously from N/S/E/W; capacity drains by 4 × `gather_rate` in one turn (clamped correctly)
- `tests/test_energy_stations_attack.py` — push moves target bot one cell; push into wall costs energy but leaves target in place
- `tests/test_energy_stations_depletion.py` — station at 0 capacity becomes `EMPTY`; `is_finished()` triggers when last station depleted
- `tests/test_energy_stations_regression.py` — identical seed + bots → identical `replay.json`

## Out of scope

- HP system or death (push is the only combat; no elimination)
- Dynamic station respawning
- Team energy pooling

## Definition of done

- [x] `code-scenarios run --scenario energy_stations --bots-dir student_bots --seed 1` completes headless with 2+ bots
- [x] `GATHER` only fires when adjacent to a station; non-adjacent GATHER → WAIT
- [x] Up to 4 simultaneous gatherers confirmed by multiside test
- [x] `ATTACK` pushes the target; blocked push consumes `attack_cost` but target does not move
- [x] Station capacity drains correctly; depleted stations removed from map; scenario ends on full depletion
- [x] `metrics.json` includes `energy_final`, `gathers`, `pushes_landed`, `pushes_blocked` per bot
- [x] `EnergyStationsView` methods accessible from starter bot; documented in template comments
- [x] UI shows station tiles with capacity indicator; bot energy bars visible during simulation
- [x] All Phase 6 tests pass

## Verification

```bash
pytest tests/test_energy_stations_setup.py tests/test_energy_stations_gather.py tests/test_energy_stations_multiside.py tests/test_energy_stations_attack.py tests/test_energy_stations_depletion.py tests/test_energy_stations_regression.py -v
code-scenarios run --scenario energy_stations --bots-dir student_bots --seed 1
code-scenarios run --scenario energy_stations --bots-dir student_bots --seed 1
# verify replay.json is identical both runs
python -m ui
# Manual: launch energy_stations from menu, confirm station tiles, energy bars, capacity overlays
```

## References

- [`engine/core/action.py`](../engine/core/action.py) — `ATTACK` (push semantics for this scenario)
- [`engine/simulation/map.py`](../engine/simulation/map.py) — `TileType.STATION` addition
- [`engine/student_api/`](../engine/student_api/) — `EnergyStationsView` subclass
- [`scenarios/resource_wars/game.py`](../scenarios/resource_wars/game.py) — reference for `ScenarioBase` pattern
- [`implementation/Phase_5.md`](Phase_5.md) — `BossFightView` pattern to follow for `EnergyStationsView`
