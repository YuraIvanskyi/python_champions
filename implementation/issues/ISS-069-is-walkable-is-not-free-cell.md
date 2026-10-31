---
id: ISS-069
area: logic
severity: med
status: fixed
---

# ISS-069: is_walkable() Means "Not An Obstacle", Not "Free Cell"

## Symptom
`GameView.is_walkable(x, y)` is True for every tile inside the map except `OBSTACLE`; it ignores other units
(and the boss). Students and the starter guides read it as "I can step there", but a move into an occupied cell is
blocked (ISS-067: 27 of 27 blocked moves had `is_walkable` True). Separately, a bot that checks `is_walkable` can still
stall in a local minimum (greedy step toward the target, Boss Fight demo `anna_bot` on 3 of 5 maps), and the platform
has no hint about it.

## Affected files
engine/student_api/view.py (`is_walkable`, `is_obstacle`); engine/i18n/guides.py; docs in features_summary_uk.md

## Fix sketch
Add `is_free(x, y)` (walkable and not occupied) or document the difference prominently in the guides and in the
card text. Consider a "stuck in local minimum" card that suggests remembering visited cells or random tie-breaking.

## Resolution
Added `GameView.is_free(x, y)` (walkable, not a pool, no other unit; `BossFightView` also excludes the boss cell). `is_walkable` docstring, guides, starters and `features_summary_uk.md` explain the difference. Not done: the optional "local minimum" card.
