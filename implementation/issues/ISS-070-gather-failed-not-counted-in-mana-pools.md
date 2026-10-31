---
id: ISS-070
area: logic
severity: med
status: fixed
---

# ISS-070: Failed GATHER Counted As Invalid Only In Resource Wars

## Symptom
`RuntimeCollector.record_turn` counts `f"{player_id}_gather_failed" in events` as an invalid action. Resource Wars
emits exactly that event, but Mana Pools emits `_gather_failed_no_capacity` and `_gather_failed_not_adjacent`, which
never match the exact-string test. The same wasted action is therefore counted in one scenario and ignored in the other,
so `invalid_action_count` and the penalties built on it are not comparable.

## Affected files
engine/analysis/runtime.py (`record_turn`); scenarios/mana_pools/game.py; scenarios/resource_wars/game.py

## Fix sketch
Match by prefix (`startswith(f"{player_id}_gather_failed")`) or emit one canonical event with a reason payload.
Decide explicitly whether a failed GATHER is an "invalid action" and document it.

## Resolution
Premise corrected: scenario events never reached `RuntimeCollector` (it only sees sandbox events), so the `_gather_failed` branch was dead in every scenario. It is removed; `invalid_action_count` now means unparseable actions only (card text updated). Failed gathers are counted from the replay by prefix (`failed_gather_count`), identically for Resource Wars and Mana Pools.
