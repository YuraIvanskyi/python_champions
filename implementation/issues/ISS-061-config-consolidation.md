---
id: ISS-061
area: config
severity: med
status: fixed
---

# ISS-061: Config Consolidation

## Symptom
Multiple scenario.toml readers; Settings incomplete.

## Affected files
engine/core/config_io.py; ui/screens/settings.py

## Fix sketch
Single facade; enable_ai/volume in Settings.
