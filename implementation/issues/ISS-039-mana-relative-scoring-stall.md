---
id: ISS-039
area: logic
severity: med
status: fixed
---

# ISS-039: Mana Relative Scoring Stall

## Symptom
Relative scores inflate gameplay; false stall feedback.

## Affected files
scenarios/mana_pools/game.py; engine/analysis/movement.py

## Fix sketch
Absolute threshold scoring; skip stall on relative scores.
