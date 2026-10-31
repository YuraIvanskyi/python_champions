---
id: ISS-071
area: feedback
severity: low
status: fixed
---

# ISS-071: Wasted GATHER / WAIT Turns Produce No Coach Card

## Symptom
Failed GATHER attempts (not on a resource, not adjacent to a pool, pool empty) and idle WAIT turns reduce the gameplay
score but have no dedicated card in `feedback.py` (no reference to `gather_failed` there). A bot that gathers on empty
tiles gets the generic repeat-action or low-score text, not the cause.

## Affected files
engine/analysis/feedback.py; engine/analysis/movement.py; engine/i18n/feedback_strings.py

## Fix sketch
Count failed gathers and WAIT turns per player in the movement/runtime metrics and add a card
("GATHER without a resource: check on_resource()/can_gather() first") with the turns listed.

## Resolution
Movement metrics add `failed_gather_count`, `failed_gather_turns`, `wait_count`; new cards "GATHER with nothing to gather" (threshold `failed_gather_warn`, default 3) and "Many idle turns" (`wait_ratio_warn`, default 0.4), both in `configs/default.toml`.
