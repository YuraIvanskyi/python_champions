---
id: ISS-067
area: feedback
severity: med
status: fixed
---

# ISS-067: "Blocked Moves" Card Blames Obstacles And Suggests is_walkable

## Symptom
`feedback.blocked_moves` says "tried to move into obstacles N% of the time" and advises `is_walkable()`. In Mana Pools
(seed 42, 60 turns, 5 demo bots) the blocked-move causes were: starter 24 obstacle + 1 player; mykhailo_bot 23 player + 4 empty
cell (simultaneous move into the same tile). For mykhailo_bot `is_walkable()` was True for all 27 blocked cells, so the
advice cannot fix the problem. The card also does not cover blocking by another unit or the map edge.

## Affected files
engine/i18n/feedback_strings.py (`feedback.blocked_moves.*`); engine/analysis/feedback.py; engine/analysis/movement.py

## Fix sketch
Record the cause of each blocked move in the turn log (obstacle / unit / edge / conflict) and choose the message by
the dominant cause: obstacles -> is_walkable; units -> check `other_units()` / `others_positions()` or wait; conflict -> note
that two players cannot enter the same tile in one turn.

## Resolution
Scenarios emit `<pid>_blocked_by_<edge|obstacle|unit|conflict>` next to `<pid>_blocked`; movement metrics store `blocked_causes`; the card text/advice follows the dominant cause (old replays without causes keep the obstacle wording).
