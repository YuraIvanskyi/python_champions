---
phase_id: phase-5
status: not_started
depends_on: [phase-2-8, phase-3-1]
source_plan: PLAN.md §16 Phase 5, §13, §18, §24
---

> **PHASE_STATUS:** `NOT_STARTED`

# Phase 5 — Tournament mode

## Goal

Support **multiple students** in one session: batch execution, rankings, reproducible replays, and teacher workflow hooks ([PLAN.md §16.5](../PLAN.md#16-development-phases), [§18](../PLAN.md#18-teacher-workflow)).

## Prerequisites

- Phase 2 complete (UI for replay browser and results display)
- Phase 3 complete (per-bot metrics and scoring)
- Phase 1 sandbox stable under repeated runs

## Setup

1. Create `student_bots/tournament/` or use flat `student_bots/*.py` for submissions.
2. Add `configs/tournament.toml` example:

   ```toml
   [tournament]
   scenario = "resource_wars"
   seed = 42
   bots_dir = "student_bots"
   parallel = false
   ```

3. Document teacher workflow in root README ([PLAN.md §18](../PLAN.md#18-teacher-workflow)).

## Implementation steps

1. **Tournament runner** in `engine/tournament/runner.py`:
   - Discover all `.py` bots in configured directory (exclude `example_bot.py` or include via flag)
   - Run each bot against same scenario + seed (or seed per bracket — document choice)
   - Sequential execution by default (`parallel = false`) for predictable classroom machines

2. **Session layout** ([PLAN.md §13](../PLAN.md#13-result-system)):

   ```text
   results/tournament_<timestamp>/
     manifest.json      # bot list, seed, scenario, timestamps
     rankings.json      # sorted by final_score
     bot_<name>/
       replay.json
       metrics.json
       logs.txt
   ```

3. **Rankings** in `engine/tournament/rankings.py`:
   - Sort by `final_score`, tie-break by gameplay_score then fewer timeouts
   - Export CSV optional for teacher spreadsheets

4. **CLI**:
   - `code-scenarios tournament --scenario resource_wars --bots-dir student_bots --seed 42`
   - Flags: `--filter name_prefix`, `--continue-on-error`

5. **Security for batch** ([PLAN.md §10](../PLAN.md#10-security-strategy)):
   - Each bot still in subprocess sandbox
   - Global tournament timeout optional
   - Failed bot → logged, score 0, continue to next

6. **Teacher workflow helpers**:
   - `code-scenarios tournament init-template` — copies starter to `student_bots/<name>.py`
   - Manifest records class/session label from `--label "Period 3"`

7. **UI: tournament mode**:
   - Menu item "Run tournament" → pick folder → progress bar
   - Leaderboard screen from `rankings.json`
   - Replay browser lists all bots in tournament folder

8. **Reproducibility** ([PLAN.md §24](../PLAN.md#24-success-criteria)):
   - Same seed + same bot files → identical `rankings.json`
   - Document in manifest which engine version / config hash was used

9. **Tests**:
   - `tests/test_tournament_discovery.py` — finds N bots in fixture dir
   - `tests/test_tournament_rankings.py` — ordering correct for fixture metrics
   - `tests/test_tournament_manifest.py` — manifest written with required fields
   - `tests/test_tournament_continue_on_error.py` — one bad bot does not stop batch

## Out of scope

- LAN multiplayer networking ([PLAN.md §21](../PLAN.md#multiplayer-networking))
- Parallel subprocess pool (optional later; not required for done)
- Team scenarios ([PLAN.md §8.4](../PLAN.md#84-team-capture) — Phase 6)

## Definition of done

- [ ] CLI runs tournament over 3+ bots in a directory
- [ ] `results/tournament_*/rankings.json` lists all participants with scores
- [ ] Each bot has isolated session subfolder with replay + metrics
- [ ] UI shows leaderboard and can open any tournament replay
- [ ] One crashing bot does not abort entire tournament (`--continue-on-error` default on)
- [ ] Re-running with same seed and files reproduces rankings
- [ ] Teacher workflow documented (select scenario → distribute template → collect → run → review)
- [ ] Phase 5 tests pass

## Verification

```bash
uv run pytest tests/test_tournament_discovery.py tests/test_tournament_rankings.py tests/test_tournament_manifest.py tests/test_tournament_continue_on_error.py -v
# Fixture bots in tests/fixtures/bots/
uv run code-scenarios tournament --scenario resource_wars --bots-dir tests/fixtures/bots --seed 99 --label test
uv run python -m ui
# Manual: open tournament results and replay browser
```

## References

- [PLAN.md §16 — Phase 5](../PLAN.md#16-development-phases)
- [PLAN.md §13 — Result System](../PLAN.md#13-result-system)
- [PLAN.md §18 — Teacher Workflow](../PLAN.md#18-teacher-workflow)
- [PLAN.md §24 — Success Criteria](../PLAN.md#24-success-criteria)
