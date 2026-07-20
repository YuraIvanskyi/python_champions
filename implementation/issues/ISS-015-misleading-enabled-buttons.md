---
id: ISS-015
area: ui
severity: med
status: fixed
---

# ISS-015: Misleading Enabled Buttons

## Symptom
Open Folder enabled with no session; Browse/Folder same icon.

## Affected files
ui/screens/scores.py; ui/screens/menu.py

## Fix sketch
Disable when no session; distinct icons.
