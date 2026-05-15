---
phase_id: phase-6
status: not_started
depends_on: [phase-5]
source_plan: PLAN.md §16 Phase 6, §8.4
---

> **PHASE_STATUS:** `NOT_STARTED`

# Phase 6 — Advanced scenarios

## Goal

Extend the scenario system with **teams, shared resources, fog of war, and communication APIs** without breaking the Phase 1 Resource Wars scenario ([PLAN.md §16.6](../PLAN.md#16-development-phases), [§8.4](../PLAN.md#84-team-capture)).

## Prerequisites

- Phase 5 complete (tournament + multi-bot infrastructure)
- Stable `ScenarioBase` API from Phase 1

## Setup

1. Create `scenarios/team_battle/` package (name per PLAN §5).
2. Add scenario-specific `scenario.toml` with team size, fog radius, shared pool settings.
3. Add starter templates: `student_bots/team_alpha.py`, `student_bots/team_beta.py` (or team API in one file per group).

## Implementation steps

1. **Extend `ScenarioBase`** (backward compatible):
   - Optional hooks: `get_visible_state(player_id)`, `get_team_resources(team_id)`, `broadcast_allowed() -> bool`
   - Default implementations preserve Phase 1 scenarios unchanged

2. **Team model** in `engine/simulation/team.py`:
   - Players belong to `team_id`
   - Shared resource pool updated by any teammate
   - Team-level score aggregation in `calculate_score()`

3. **Fog of war** in `engine/simulation/visibility.py`:
   - `game_state` for each bot includes only `visible_tiles` within radius ([PLAN.md §17 example](../PLAN.md#game-state))
   - Hidden entities omitted or masked
   - Replay stores full map; viewer can toggle "fog" for teaching

4. **Communication API** ([PLAN.md §8.4](../PLAN.md#84-team-capture)):
   - Per-turn limited message: `send_message(team_id, payload)` with size cap (e.g. 64 chars or structured dict)
   - Messages delivered to teammates at start of next turn
   - Log messages in replay for debugging

5. **Team Capture scenario** under `scenarios/team_battle/`:
   - Two teams, two bots each (or 2v2 tournament mode)
   - Objective: capture flag or control zone together
   - Concepts: modular design, cooperation (align with PLAN §8.4)

6. **Loader restrictions**:
   - Document allowed imports for communication helpers
   - Sandbox still applies per bot subprocess

7. **Tournament integration**:
   - `code-scenarios tournament --scenario team_battle` runs teams (manifest lists teams not only individuals)
   - Rank by team score

8. **UI updates**:
   - Fog rendering (unexplored tiles dimmed)
   - Team colors and shared resource HUD
   - Optional message log panel

9. **Regression tests**:
   - `tests/test_resource_wars_regression.py` — Phase 1 scenario still passes unchanged
   - `tests/test_team_battle.py` — team scoring and fog visibility
   - `tests/test_communication.py` — message delivered next turn, size limit enforced

10. **Documentation**:
    - New section in root README: "Writing advanced scenarios"
    - Student handout for team API vs solo API

## Out of scope

- Web version / FastAPI ([PLAN.md §21](../PLAN.md#web-version))
- Docker sandbox ([PLAN.md §10 Later Stages](../PLAN.md#later-stages))
- Curriculum analytics ([PLAN.md §21](../PLAN.md#curriculum-analytics))

## Definition of done

- [ ] `scenarios/team_battle/` runs headless and in GUI
- [ ] Teams share resources; team score computed correctly
- [ ] Fog limits `visible_tiles` in student `game_state`
- [ ] Communication API works with documented limits
- [ ] `resource_wars` regression tests still pass (no breaking API change)
- [ ] Tournament mode supports team scenario manifest
- [ ] UI shows fog and team HUD for team_battle
- [ ] Phase 6 tests pass

## Verification

```bash
uv run pytest tests/test_resource_wars_regression.py tests/test_team_battle.py tests/test_communication.py -v
uv run code-scenarios run --scenario team_battle --bot student_bots/team_alpha.py --seed 7
uv run code-scenarios tournament --scenario team_battle --bots-dir student_bots --seed 7 --label team_test
uv run python -m ui
# Manual: verify fog and team resources in simulation viewer
```

## References

- [PLAN.md §16 — Phase 6](../PLAN.md#16-development-phases)
- [PLAN.md §8.4 — Team Capture](../PLAN.md#84-team-capture)
- [PLAN.md §5 — Proposed System Architecture](../PLAN.md#5-proposed-system-architecture)
- [PLAN.md §17 — Suggested Internal APIs](../PLAN.md#17-suggested-internal-apis)
