"""Game participants and bot bindings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from engine.core.action import Action


class TurnCallable(Protocol):
    def __call__(self, game_state: dict[str, Any]) -> str | Action: ...


@dataclass
class Player:
    player_id: str
    display_name: str
    is_student: bool = False


@dataclass
class Bot:
    player: Player
    make_turn: TurnCallable
    source_path: str | None = None
