"""Outcome of a single simulation turn."""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.core.action import Action


@dataclass
class TurnResult:
    turn_number: int
    actions: dict[str, Action]
    scores: dict[str, int]
    events: list[str] = field(default_factory=list)
