---
id: ISS-014
area: ui
severity: med
status: fixed
---

# ISS-014: Button Mouseup Without Press

## Symptom
Button/ListRow activate on release without press tracking.

## Affected files
ui/widgets/controls.py

## Fix sketch
Track press-in-rect before click.
