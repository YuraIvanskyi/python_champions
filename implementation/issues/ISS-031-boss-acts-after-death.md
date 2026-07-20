---
id: ISS-031
area: logic
severity: high
status: fixed
---

# ISS-031: Boss Acts After Death

## Symptom
Boss still attacks after HP hits 0 same turn.

## Affected files
scenarios/boss_fight/game.py

## Fix sketch
Skip boss turn when boss_hp<=0 before attacks.
