---
phase_id: phase-1
status: done
depends_on: [phase-0]
source_plan: PLAN.md §16 Phase 1, §6, §5, §10, §12–14, §17, §22
---

> **PHASE_STATUS:** `DONE`

# Phase 1 — Minimal prototype

## Goal

Deliver a **headless** single-player turn simulation: basic engine, one scenario, dynamic student bot loading, terminal output, and seeded deterministic turns. No GUI yet ([PLAN.md §16.1](../PLAN.md#16-development-phases)).

## Prerequisites

- Phase 0 complete (`phase-0` status `done` in [PHASE_REGISTRY.yaml](PHASE_REGISTRY.yaml))
- Virtual environment with dependencies installed

## Setup

1. Confirm Phase 0 verification commands pass.
2. Copy `configs/default.toml` to `configs/dev.toml` if you need local overrides (optional).
3. Create placeholder bot: `student_bots/example_bot.py` (starter template for students).

## Implementation steps

1. **Engine core abstractions** in `engine/core/` ([PLAN.md §6.1](../PLAN.md#61-engine-core)):
   - `Game` — owns scenario, players, turn counter, RNG seed
   - `Player` / `Bot` — participant binding to loaded code
   - `TurnResult` — outcome of one turn (actions applied, events)
   - `Action` — validated action enum or small dataclass (e.g. `MOVE_RIGHT`)

2. **Scenario interface** in `engine/core/scenario.py` ([PLAN.md §6.4](../PLAN.md#64-scenario-system)):

   ```python
   class ScenarioBase:
       def setup(self): ...
       def apply_turn(self, actions): ...
       def calculate_score(self): ...
       def is_finished(self) -> bool: ...
   ```

3. **First scenario: Resource Wars (minimal)** under `scenarios/resource_wars/` ([PLAN.md §8.1](../PLAN.md#81-resource-wars)):
   - Small grid map (e.g. 8×8)
   - Tiles: empty, resource, obstacle
   - One student bot + one built-in AI opponent
   - Actions: move (4 directions), gather, wait
   - Victory: max turns or score threshold
   - Export scenario via `scenario.toml` or `__init__.py` registry

4. **Map and entities** in `engine/simulation/`:
   - `Map` — grid storage, bounds checks
   - `Entity` — position, type, owner
   - State updates only through scenario + engine (no student access to internals)

5. **Student code loader** in `engine/core/loader.py` ([PLAN.md §6.2](../PLAN.md#62-student-code-loader)):
   - Load single `.py` file via `importlib`
   - Support **simple API**: `def make_turn(game_state) -> str | Action`
   - Support **advanced API**: `class StudentBot(BotBase): def make_turn(self, state): ...` ([PLAN.md §17](../PLAN.md#17-suggested-internal-apis))
   - Expose **readonly** `game_state` dict to students ([PLAN.md §17](../PLAN.md#17-suggested-internal-apis)) — e.g. position, resources, visible tiles; never engine internals

6. **Sandbox layer** in `engine/sandbox/` ([PLAN.md §6.3](../PLAN.md#63-sandbox-layer), [§10](../PLAN.md#10-security-strategy)):
   - Run `make_turn` in **subprocess** with strict wall-clock timeout from `configs/default.toml` (`turn_timeout_ms`)
   - Kill on timeout; return safe default action or forfeit turn
   - Restrict imports (denylist: `os`, `subprocess`, `socket`, `sys` mutations, etc.) — document allowed set for students
   - No filesystem/network from student code in this phase

7. **Deterministic RNG** ([PLAN.md §3.2](../PLAN.md#32-deterministic-simulations)):
   - Accept `--seed` on CLI; default fixed seed for reproducibility
   - Pass seed into scenario for any random events

8. **Turn loop** in `engine/core/game.py`:
   - Load config TOML → instantiate scenario → load bots → loop until `max_turns` or `is_finished()`
   - Collect per-turn log (actions, scores)

9. **Built-in AI opponent** in `engine/simulation/simple_ai.py`:
   - Greedy or random legal moves (seeded) so solo testing works without a second student file

10. **CLI** in `engine/cli.py`:
    - `code-scenarios run --scenario resource_wars --bot student_bots/example_bot.py [--seed N]`
    - Terminal output: turn number, actions, score summary

11. **Replay stub** ([PLAN.md §13–14](../PLAN.md#13-result-system)):
    - After run, write `results/session_<timestamp>/replay.json` with: seed, scenario id, turns[], final scores
    - Write `results/session_<timestamp>/logs.txt` with human-readable trace

12. **Example student bot** `student_bots/example_bot.py`:
    - Minimal working `make_turn` (e.g. move toward nearest resource)
    - Comments pointing students to allowed API

13. **Tests** in `tests/`:
    - `test_engine_turns.py` — 10 turns headless, no crash
    - `test_loader.py` — loads example bot
    - `test_sandbox_timeout.py` — infinite loop bot times out safely
    - `test_replay_written.py` — replay.json exists after CLI run

## Out of scope

- Pygame UI (Phase 2)
- Ruff/Radon analysis (Phase 3)
- Tournament / batch runs (Phase 5)
- LLM feedback (Phase 4)

## Definition of done

- [x] `engine/core/` turn loop runs headless for at least 10 turns without error
- [x] `scenarios/resource_wars/` loads and runs via CLI
- [x] Student bot loads from `student_bots/` via importlib (simple or class API)
- [x] Subprocess sandbox enforces timeout on malicious/slow bot
- [x] Same `--seed` produces identical `replay.json` on two runs
- [x] Built-in AI opponent participates in simulation
- [x] `results/<session>/replay.json` contains seed, turns, and scores
- [x] Terminal CLI prints readable turn-by-turn summary
- [x] `student_bots/example_bot.py` runs successfully as reference submission
- [x] All Phase 1 tests pass

## Verification

```bash
uv run pytest tests/test_engine_turns.py tests/test_loader.py tests/test_sandbox_timeout.py tests/test_replay_written.py -v
uv run code-scenarios run --scenario resource_wars --bot student_bots/example_bot.py --seed 42
uv run code-scenarios run --scenario resource_wars --bot student_bots/example_bot.py --seed 42
# Compare two replay.json files — should be identical
```

## References

- [PLAN.md §16 — Phase 1](../PLAN.md#16-development-phases)
- [PLAN.md §6 — Core Modules](../PLAN.md#6-core-modules)
- [PLAN.md §10 — Security Strategy](../PLAN.md#10-security-strategy)
- [PLAN.md §12 — Data Flow](../PLAN.md#12-data-flow)
- [PLAN.md §13–14 — Result / Replay](../PLAN.md#13-result-system)
- [PLAN.md §17 — Suggested Internal APIs](../PLAN.md#17-suggested-internal-apis)
- [PLAN.md §22 — Recommended First MVP](../PLAN.md#22-recommended-first-mvp)
