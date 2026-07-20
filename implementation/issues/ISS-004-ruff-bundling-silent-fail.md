---
id: ISS-004
area: build
severity: med
status: fixed
---

# ISS-004: Ruff Bundling Silent Fail

## Symptom
Ruff missing in dist returns empty violations silently.

## Affected files
packaging/code_scenarios.spec; engine/analysis/static.py

## Fix sketch
Assert ruff.exe in build; surface missing tool in metrics.
