---
id: ISS-016
area: ui
severity: med
status: fixed
---

# ISS-016: Uk Label Truncation

## Symptom
Fixed button widths clip Ukrainian labels.

## Affected files
ui/screens/*; ui/theme.py

## Fix sketch
Locale-aware min widths from label metrics.
