"""Built-in greedy opponent for solo testing."""

from __future__ import annotations

import random
from typing import Any

from engine.core.action import Action


def greedy_turn(game_state: dict[str, Any], rng: random.Random) -> Action:
    position = game_state["position"]
    px, py = position[0], position[1]
    resources_on_tile = game_state.get("on_resource", False)
    if resources_on_tile:
        return Action.GATHER

    best: tuple[int, Action] | None = None
    for action, dx, dy in (
        (Action.MOVE_UP, 0, -1),
        (Action.MOVE_DOWN, 0, 1),
        (Action.MOVE_LEFT, -1, 0),
        (Action.MOVE_RIGHT, 1, 0),
    ):
        nx, ny = px + dx, py + dy
        if not _is_walkable(game_state, nx, ny):
            continue
        dist = _distance_to_nearest_resource(game_state, nx, ny)
        if best is None or dist < best[0] or (dist == best[0] and rng.random() < 0.5):
            best = (dist, action)

    if best is not None:
        return best[1]
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


def _distance_to_nearest_resource(game_state: dict[str, Any], x: int, y: int) -> int:
    best = 10_000
    for tile in game_state["visible_tiles"]:
        if tile["type"] != "resource":
            continue
        dist = abs(tile["x"] - x) + abs(tile["y"] - y)
        best = min(best, dist)
    return best
