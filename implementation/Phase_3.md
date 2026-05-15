---
phase_id: phase-3
status: not_started
depends_on: [phase-1]
source_plan: PLAN.md §16 Phase 3, §6.5, §15, §22, §24
---

> **PHASE_STATUS:** `NOT_STARTED`

# Phase 3 — Analysis system

## Goal

Integrate **static and runtime analysis** (Ruff, Radon, AST), produce student-friendly feedback from metrics, and implement configurable combined scoring ([PLAN.md §16.3](../PLAN.md#16-development-phases), [§6.5](../PLAN.md#65-analysis-engine), [§15](../PLAN.md#15-scoring-system)).

Completing Phases 0–3 satisfies [PLAN.md §22 MVP](../PLAN.md#22-recommended-first-mvp).

## Prerequisites

- Phase 1 complete (CLI run produces `results/` sessions)
- Phase 2 not required for this phase (analysis can run headless first; UI panel optional hook)

## Setup

1. Confirm Phase 1 verification passes.
2. Add analysis config section to `configs/default.toml` if not already present:

   ```toml
   [analysis]
   enable_static_analysis = true
   enable_ai = false
   ruff_select = ["E", "F", "W"]
   ```

3. Add `engine/analysis/` package files (empty modules from Phase 0).

## Implementation steps

1. **Static analysis runner** in `engine/analysis/static.py`:
   - Run **Ruff** on student bot path; capture violations (rule, line, message)
   - Run **Radon** for cyclomatic complexity, maintainability index per function
   - Use **AST** (`ast` module) for: nesting depth, function lengths, unused names (basic visit), forbidden constructs list from config

2. **Runtime metrics collector** in `engine/analysis/runtime.py` ([PLAN.md §6.5 Runtime](../PLAN.md#runtime-analysis)):
   - Per session: execution time per turn, crash count, invalid action count, timeout count
   - Hook into existing turn loop / sandbox (Phase 1)

3. **Educational feedback layer** in `engine/analysis/feedback.py` ([PLAN.md §6.5 Educational](../PLAN.md#educational-feedback-layer)):
   - Map metric thresholds → plain-language hints (templates, no LLM)
   - Example: high complexity → "Try splitting logic into smaller functions."
   - Store `feedback.json` or embed in `metrics.json`

4. **Scoring module** in `engine/scoring/` ([PLAN.md §15](../PLAN.md#15-scoring-system)):
   - `gameplay_score` from scenario `calculate_score()`
   - `code_quality_score` from normalized static metrics (0–100 scale; document formula)
   - `final_score = gameplay_score * 0.7 + code_quality * 0.3` — weights overridable in scenario config

5. **Scenario scoring config** in `scenarios/resource_wars/scenario.toml` (or equivalent):
   - `gameplay_weight`, `code_weight`, objective weights

6. **Pipeline integration** after simulation ([PLAN.md §12](../PLAN.md#12-data-flow)):
   - On `code-scenarios run` completion: run analysis → write `results/session_*/metrics.json`
   - Structure:

     ```json
     {
       "gameplay": {},
       "static": {},
       "runtime": {},
       "scores": { "gameplay": 0, "code_quality": 0, "final": 0 },
       "feedback": []
     }
     ```

7. **CLI flags**:
   - `--no-analysis` to skip for fast runs
   - `--analysis-only --bot path` to analyze without full simulation (optional)

8. **Headless report** in terminal:
   - Print top 3 feedback items + final score after run

9. **UI hook** (if Phase 2 done): analysis panel on score screen reading `metrics.json`; if Phase 2 not done, skip UI but keep JSON output

10. **Tests**:
    - `tests/test_static_analysis.py` — sample bot with known Ruff issue detected
    - `tests/test_scoring_formula.py` — weights produce expected final score
    - `tests/test_metrics_output.py` — run produces `metrics.json` with required keys
    - `tests/test_feedback_templates.py` — high complexity triggers expected message

## Out of scope

- LLM summaries (Phase 4)
- Tournament batch reports (Phase 5)
- Auto-fixing student code (forbidden per PLAN §7)

## Definition of done

- [ ] Ruff, Radon, and AST metrics collected for student bot file
- [ ] Runtime metrics recorded during simulation
- [ ] `metrics.json` written under each session in `results/`
- [ ] At least 5 feedback templates cover common student issues
- [ ] Combined score uses configurable weights (default 0.7 / 0.3)
- [ ] CLI prints understandable summary for beginners ([PLAN.md §24](../PLAN.md#24-success-criteria))
- [ ] `enable_static_analysis = false` in config skips static pass
- [ ] Phase 3 tests pass
- [ ] MVP checklist from PLAN §22 met for analysis portion

## Verification

```bash
uv run pytest tests/test_static_analysis.py tests/test_scoring_formula.py tests/test_metrics_output.py tests/test_feedback_templates.py -v
uv run code-scenarios run --scenario resource_wars --bot student_bots/example_bot.py --seed 1
# Confirm results/session_*/metrics.json exists and contains scores + feedback
cat results/session_*/metrics.json
```

## References

- [PLAN.md §16 — Phase 3](../PLAN.md#16-development-phases)
- [PLAN.md §6.5 — Analysis Engine](../PLAN.md#65-analysis-engine)
- [PLAN.md §15 — Scoring System](../PLAN.md#15-scoring-system)
- [PLAN.md §22 — Recommended First MVP](../PLAN.md#22-recommended-first-mvp)
- [PLAN.md §24 — Success Criteria](../PLAN.md#24-success-criteria)
