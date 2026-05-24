"""Built-in opponent profiles and AI selection."""

from __future__ import annotations

import random
from collections.abc import Callable
from typing import Any

from engine.core.action import Action
from engine.core.bot_profile import project_root
from engine.core.player import Player
from engine.simulation.dumb_ai import dumb_turn
from engine.simulation.simple_ai import greedy_turn

OPPONENT_MODES = ("greedy", "dumb")

_BUILTIN_ICONS: dict[str, str] = {
    "greedy": "ui/assets/icons/rival.png",
    "dumb": "ui/assets/icons/rookie.png",
}

_BUILTIN_NAMES: dict[str, str] = {
    "greedy": "Rival",
    "dumb": "Rookie",
}

def normalize_opponent_mode(mode: str | None, *, default: str = "greedy") -> str:
    if mode is None or mode == "":
        return default
    key = mode.strip().lower()
    if key not in OPPONENT_MODES:
        raise ValueError(f"Unknown opponent {mode!r}; use greedy or dumb")
    return key


def builtin_icon_path(mode: str) -> str | None:
    rel = _BUILTIN_ICONS.get(mode)
    if rel is None:
        return None
    path = project_root() / rel
    return str(path) if path.is_file() else None


def opponent_player(mode: str) -> Player:
    normalized = normalize_opponent_mode(mode)
    return Player(
        player_id="opponent",
        display_name=_BUILTIN_NAMES[normalized],
        is_student=False,
        icon_path=builtin_icon_path(normalized),
    )


def resolve_ai_turn(mode: str) -> Callable[[dict[str, Any], random.Random], Action]:
    normalized = normalize_opponent_mode(mode)
    if normalized == "dumb":
        return dumb_turn
    return greedy_turn
