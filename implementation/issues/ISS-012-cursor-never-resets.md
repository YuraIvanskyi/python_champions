---
id: ISS-012
area: ui
severity: med
status: fixed
---

# ISS-012: Cursor Never Resets

## Symptom
Hand cursor sticks after hover.

## Affected files
ui/widgets/controls.py; ui/screens/menu.py

## Fix sketch
Central cursor reset each frame.
