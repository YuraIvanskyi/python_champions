---
id: ISS-052
area: feedback
severity: med
status: fixed
---

# ISS-052: Scores Coach Wrong Player

## Symptom
Scores->Coach ignores clicked row player_id.

## Affected files
ui/screens/scores.py; ui/app.py

## Fix sketch
Pass player_id to goto_coach.
