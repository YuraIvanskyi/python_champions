---
id: ISS-035
area: logic
severity: med
status: fixed
---

# ISS-035: Mana Pools Energy Edge Cases

## Symptom
Discounted attack with 1-2 energy; gather at max counted.

## Affected files
scenarios/mana_pools/game.py

## Fix sketch
Require full attack_cost; skip gather increment at max.
