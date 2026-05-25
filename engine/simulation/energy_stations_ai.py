"""Built-in opponents for Mana Pools solo practice."""

from __future__ import annotations

import random
from typing import Any

from engine.core.action import Action


def _is_walkable(game_state: dict[str, Any], x: int, y: int) -> bool:
    width = game_state["map_width"]
    height = game_state["map_height"]
    if x < 0 or y < 0 or x >= width or y >= height:
        return False
    for tile in game_state["visible_tiles"]:
        if tile["x"] == x and tile["y"] == y:
            return tile["type"] not in ("obstacle", "station")
    return False


def _nearest_station(
    game_state: dict[str, Any],
) -> tuple[int, int] | None:
    position = game_state["position"]
    px, py = position[0], position[1]
    stations = game_state.get("stations", [])
    best: tuple[int, tuple[int, int]] | None = None
    for station in stations:
        if not isinstance(station, dict):
            continue
        cap = int(station.get("capacity", 0))
        if cap <= 0:
            continue
        sx, sy = int(station["x"]), int(station["y"])
        dist = abs(sx - px) + abs(sy - py)
        if best is None or dist < best[0]:
            best = (dist, (sx, sy))
    return best[1] if best else None


def _move_toward(position: list[int], target: tuple[int, int]) -> Action:
    px, py = position[0], position[1]
    tx, ty = target
    if tx > px:
        return Action.MOVE_RIGHT
    if tx < px:
        return Action.MOVE_LEFT
    if ty > py:
        return Action.MOVE_DOWN
    return Action.MOVE_UP


def greedy_energy_turn(game_state: dict[str, Any], rng: random.Random) -> Action:
    if game_state.get("adjacent_stations"):
        return Action.GATHER

    nearest = _nearest_station(game_state)
    if nearest is None:
        return Action.WAIT

    position = game_state["position"]
    action = _move_toward(position, nearest)
    px, py = position[0], position[1]
    deltas = {
        Action.MOVE_UP: (0, -1),
        Action.MOVE_DOWN: (0, 1),
        Action.MOVE_LEFT: (-1, 0),
        Action.MOVE_RIGHT: (1, 0),
    }
    dx, dy = deltas[action]
    if _is_walkable(game_state, px + dx, py + dy):
        return action

    legal: list[Action] = []
    for candidate, cdx, cdy in (
        (Action.MOVE_UP, 0, -1),
        (Action.MOVE_DOWN, 0, 1),
        (Action.MOVE_LEFT, -1, 0),
        (Action.MOVE_RIGHT, 1, 0),
    ):
        if _is_walkable(game_state, px + cdx, py + cdy):
            legal.append(candidate)
    return rng.choice(legal) if legal else Action.WAIT


def dumb_energy_turn(game_state: dict[str, Any], rng: random.Random) -> Action:
    if game_state.get("adjacent_stations") and rng.random() < 0.25:
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
        if _is_walkable(game_state, px + dx, py + dy):
            legal.append(action)

    return rng.choice(legal) if legal else Action.WAIT
