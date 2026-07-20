---
id: ISS-010
area: ui
severity: high
status: fixed
---

# ISS-010: Layout In Draw Ghost Clicks

## Symptom
Button rects updated in draw() but events run first.

## Affected files
ui/screens/*.py

## Fix sketch
Layout in on_enter and before handle_event.
