---
id: ISS-037
area: logic
severity: med
status: fixed
---

# ISS-037: Boss Scoring Rounding Metrics

## Symptom
Damage share rounding; boss_metrics not in metrics.json.

## Affected files
scenarios/boss_fight/game.py; engine/core/live_game.py

## Fix sketch
Fix rounding; wire boss_metrics.
