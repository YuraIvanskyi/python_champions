---
id: ISS-040
area: logic
severity: low
status: fixed
---

# ISS-040: Resource Wars Edge Cases

## Symptom
Silent ignore of wrong actions; placement undercount; ties.

## Affected files
scenarios/resource_wars/game.py

## Fix sketch
Emit events; retry placement; document ties.
