---
id: ISS-050
area: feedback
severity: high
status: fixed
---

# ISS-050: Bot Source Not Snapshotted

## Symptom
Coach reads live bot path; breaks if file moved.

## Affected files
engine/core/session.py; ui/coach_data.py

## Fix sketch
Copy bots/{id}.py into session; update bot_files.
