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


def parse_action(value: str | Action) -> Action:
    if isinstance(value, Action):
        return value
    normalized = str(value).strip().upper()
    try:
        return Action(normalized)
    except ValueError as exc:
        raise ValueError(f"Unknown action: {value!r}") from exc
