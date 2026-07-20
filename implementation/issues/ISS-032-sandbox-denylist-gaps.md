---
id: ISS-032
area: logic
severity: high
status: fixed
---

# ISS-032: Sandbox Denylist Gaps

## Symptom
__import__/eval/exec not blocked at load.

## Affected files
engine/core/loader.py

## Fix sketch
AST checks for Call nodes; unify denylist with config.
