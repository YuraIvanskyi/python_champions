---
id: ISS-063
area: logic
severity: med
status: fixed
---

# ISS-063: First Turn Times Out On Worker Cold Start

## Symptom
The 200 ms per-turn budget (`turn_timeout_ms`) also covers worker start-up (interpreter start, imports of `engine.*`,
bot load) on turn 1. In a slow environment the first turn regularly ends with `sandbox_timeout` -> WAIT and
`timeout_count` = 1 for a perfectly correct bot (reproduced with a control bot; turns 2-10 normal).
A timeout caps `code_quality` at 50 and can appear as a student's fault.

## Affected files
engine/sandbox/runner.py (`SandboxedBot.__init__`, `_start_worker`, `run_turn`); engine/core/config.py

## Fix sketch
Start the worker eagerly and wait for a "ready" handshake line (after `load_bot`) before turn 1; apply the 200 ms
limit only to `make_turn`. Optionally give turn 1 a separate warm-up allowance.

## Resolution
Worker sends `{"ready": true}` after `load_bot`; `SandboxedBot` waits for it (new `engine.worker_startup_timeout_ms`, default 5000) before turn 1, so `turn_timeout_ms` covers `make_turn` only.
