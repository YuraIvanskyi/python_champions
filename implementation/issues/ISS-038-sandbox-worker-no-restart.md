---
id: ISS-038
area: logic
severity: med
status: fixed
---

# ISS-038: Sandbox Worker No Restart

## Symptom
Worker killed on timeout never restarted; timeout no CQ cap.

## Affected files
engine/sandbox/runner.py; engine/scoring/combined.py

## Fix sketch
Restart worker on timeout; cap CQ on timeouts too.
