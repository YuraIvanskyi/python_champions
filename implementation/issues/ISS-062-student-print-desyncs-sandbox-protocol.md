---
id: ISS-062
area: logic
severity: high
status: fixed
---

# ISS-062: Student print() Desyncs Sandbox Protocol

## Symptom
A bot that calls `print()` inside `make_turn` (typical student debugging) breaks the worker protocol:
the worker writes one JSON line per turn to the same stdout, so the host reads the student's text first.
Reproduced (Resource Wars, seed 7, 10 turns, bot with `print("debug:", ...)`): every odd turn gives
`bot_error:invalid_json` -> WAIT, every even turn returns the previous turn's JSON (answers lag by one turn).
`crash_count` = 5 of 10, so `code_quality` is capped at 50 and the bot loses half its moves for a harmless print.
Control bot without print: no errors.

## Affected files
engine/sandbox/worker_loop.py; engine/sandbox/runner.py (`_readline_with_timeout`, `run_turn`)

## Fix sketch
In the worker, keep the real stdout for the protocol and redirect `sys.stdout` to stderr (or a buffer) while
`bot.make_turn` runs; optionally show captured prints in the Code Coach as "debug output". Alternatively tag protocol
lines with a prefix and skip non-protocol lines in the host. Add a regression test with a printing bot.

## Resolution
Worker keeps the real stdout for the protocol only; student `print()` (import time and `make_turn`) and stderr go to a null sink. Regression: `tests/test_sandbox_timeout.py::test_student_print_does_not_desync_protocol`.
