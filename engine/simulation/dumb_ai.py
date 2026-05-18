"""Weak training opponent — random movement, rarely gathers."""

from __future__ import annotations

import random
from typing import Any

from engine.core.action import Action


def dumb_turn(game_state: dict[str, Any], rng: random.Random) -> Action:
    if game_state.get("on_resource") and rng.random() < 0.2:
        return Action.GATHER

    if rng.random() < 0.35:
        return Action.WAIT

    position = game_state["position"]
    px, py = position[0], position[1]
    legal: list[Action] = []
    for action, dx, dy in (
        (Action.MOVE_UP, 0, -1),
        (Action.MOVE_DOWN, 0, 1),
        (Action.MOVE_LEFT, -1, 0),
        (Action.MOVE_RIGHT, 1, 0),
    ):
        nx, ny = px + dx, py + dy
        if _is_walkable(game_state, nx, ny):
            legal.append(action)

    if legal:
        return rng.choice(legal)
    return Action.WAIT


def _is_walkable(game_state: dict[str, Any], x: int, y: int) -> bool:
    width = game_state["map_width"]
    height = game_state["map_height"]
    if x < 0 or y < 0 or x >= width or y >= height:
        return False
    for tile in game_state["visible_tiles"]:
        if tile["x"] == x and tile["y"] == y:
            return tile["type"] != "obstacle"
    return False
