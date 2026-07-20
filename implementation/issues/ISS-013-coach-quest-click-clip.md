---
id: ISS-013
area: ui
severity: med
status: fixed
---

# ISS-013: Coach Quest Click Clip

## Symptom
Quest card hits ignore viewport clip.

## Affected files
ui/screens/coach.py

## Fix sketch
Require collidepoint with quests panel rect.
