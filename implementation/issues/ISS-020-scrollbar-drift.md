---
id: ISS-020
area: style
severity: med
status: fixed
---

# ISS-020: Scrollbar Drift

## Symptom
Four different scrollbar implementations.

## Affected files
ui/skin/chrome.py; ui/screens/scores.py

## Fix sketch
Unify on skin.draw_scrollbar.
