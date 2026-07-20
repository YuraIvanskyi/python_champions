---
id: ISS-001
area: build
severity: high
status: fixed
---

# ISS-001: Frozen Sandbox Spawns Gui Exe

## Symptom
Sandbox uses sys.executable -m when frozen; GUI exe respawns instead of worker.

## Affected files
engine/sandbox/runner.py; packaging/launcher_gui.py

## Fix sketch
Add --sandbox-worker argv dispatch in launcher; spawn exe with flag when frozen.
