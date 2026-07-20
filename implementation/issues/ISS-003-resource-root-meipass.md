---
id: ISS-003
area: build
severity: med
status: fixed
---

# ISS-003: Resource Root Meipass

## Symptom
resource_root ignores sys._MEIPASS; __file__ asset loads fragile.

## Affected files
engine/paths.py; ui/render/*.py

## Fix sketch
Use _MEIPASS when frozen; route assets through resource_path().
