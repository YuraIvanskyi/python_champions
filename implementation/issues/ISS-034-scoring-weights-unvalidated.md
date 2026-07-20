---
id: ISS-034
area: logic
severity: med
status: fixed
---

# ISS-034: Scoring Weights Unvalidated

## Symptom
Weights not validated; scoring ignores user scenario.toml when frozen.

## Affected files
engine/scoring/weights.py

## Fix sketch
Validate sum==1; use scenario_toml_read_path.
