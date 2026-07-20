---
id: ISS-030
area: logic
severity: high
status: fixed
---

# ISS-030: Boss Difficulty Not In Replay

## Symptom
boss_difficulty not stored/restored in replay.

## Affected files
engine/core/session.py; engine/core/replay.py

## Fix sketch
Persist in replay.json; restore on ReplaySession.
