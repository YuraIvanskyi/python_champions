---
id: ISS-002
area: build
severity: high
status: fixed
---

# ISS-002: Writable Root Appdata

## Symptom
Results/settings write next to exe; fails under Program Files.

## Affected files
engine/paths.py; engine/core/config_io.py

## Fix sketch
Use LOCALAPPDATA/CodeScenarios; seed configs on first run.
