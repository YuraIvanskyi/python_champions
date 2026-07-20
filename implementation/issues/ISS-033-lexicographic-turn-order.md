---
id: ISS-033
area: logic
severity: high
status: fixed
---

# ISS-033: Lexicographic Turn Order

## Symptom
opponent acts before student; p10 before p2.

## Affected files
scenarios/*/game.py; engine/core/loader.py

## Fix sketch
Use setup order with zero-padded ids.
