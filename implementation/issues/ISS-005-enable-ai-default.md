---
id: ISS-005
area: build
severity: med
status: fixed
---

# ISS-005: Enable Ai Default

## Symptom
Shipped default.toml has enable_ai=true vs code False.

## Affected files
configs/default.toml; ui/screens/settings.py

## Fix sketch
Ship false; add Settings toggle.
