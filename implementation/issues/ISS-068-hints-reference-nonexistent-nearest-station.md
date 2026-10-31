---
id: ISS-068
area: feedback
severity: med
status: fixed
---

# ISS-068: Hints Recommend state.nearest_station() Which Does Not Exist

## Symptom
Coach cards (no_target, no_helpers, no_branching; en and uk) tell the student to use `state.nearest_station()`.
No view defines it: `GameView` has `resource_tiles()`, `ManaPoolsView` has `nearest_pool()`, `BossFightView` has neither.
Following the hint raises AttributeError -> crash -> quality capped at 50. `_GOAL_HELPERS` in the static movement
heuristic also lists legacy names (`nearest_station`, `adjacent_stations`, `stations`) that students cannot call.

## Affected files
engine/i18n/feedback_strings.py (lines with `nearest_station`); engine/analysis/static.py (`_GOAL_HELPERS`); engine/student_api/*.py

## Fix sketch
Scenario-aware hints: Resource Wars -> `resource_tiles()` / `has_resource_at()`; Mana Pools -> `nearest_pool()`;
Boss Fight -> `is_boss_adjacent()`, `boss_x()`. Or add a real `nearest_resource()` helper and use it everywhere. Add a test that
every API name mentioned in the catalogs exists in the views.

## Resolution
Hints use a `{helpers}` placeholder filled per scenario (`SCENARIO_GOAL_HELPERS`); `generate_feedback_items(..., scenario_id=)` is wired from the pipeline. Legacy names removed from `_GOAL_HELPERS`. `test_api_names_in_catalogs_exist_on_views` guards against drift.
