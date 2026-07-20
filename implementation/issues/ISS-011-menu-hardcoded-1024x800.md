---
id: ISS-011
area: ui
severity: high
status: fixed
---

# ISS-011: Menu Hardcoded 1024X800

## Symptom
Menu geometry assumes fixed 1024x800.

## Affected files
ui/screens/menu.py

## Fix sketch
Derive from surface.get_width/height().
