"""Validated player actions."""

from __future__ import annotations

from enum import StrEnum


class Action(StrEnum):
    MOVE_UP = "MOVE_UP"
    MOVE_DOWN = "MOVE_DOWN"
    MOVE_LEFT = "MOVE_LEFT"
    MOVE_RIGHT = "MOVE_RIGHT"
    GATHER = "GATHER"
    WAIT = "WAIT"
    # boss_fight: melee attack on adjacent boss; energy_stations: push adjacent enemy one cell away
    ATTACK = "ATTACK"
    # boss_fight only: restore heal_amount HP to self
    HEAL_SELF = "HEAL_SELF"
    # boss_fight only: restore heal_amount HP to the living ally with lowest current HP (auto-targeted)
    HEAL_ALLY = "HEAL_ALLY"


def parse_action(value: str | Action) -> Action:
    if isinstance(value, Action):
        return value
    normalized = str(value).strip().upper()
    try:
        return Action(normalized)
    except ValueError as exc:
        raise ValueError(f"Unknown action: {value!r}") from exc
