"""Built-in ally bots for Boss Fight solo practice."""

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
            return tile["type"] != "obstacle"
    return False


def _boss_position(game_state: dict[str, Any]) -> tuple[int, int]:
    boss = game_state.get("boss_position")
    if isinstance(boss, dict):
        return int(boss["x"]), int(boss["y"])
    opp = game_state.get("opponent_position", [0, 0])
    return int(opp[0]), int(opp[1])


def _is_boss_adjacent(game_state: dict[str, Any]) -> bool:
    px, py = game_state["position"]
    bx, by = _boss_position(game_state)
    return abs(px - bx) + abs(py - by) == 1


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


def _legal_moves(game_state: dict[str, Any]) -> list[Action]:
    px, py = game_state["position"]
    legal: list[Action] = []
    for action, dx, dy in (
        (Action.MOVE_UP, 0, -1),
        (Action.MOVE_DOWN, 0, 1),
        (Action.MOVE_LEFT, -1, 0),
        (Action.MOVE_RIGHT, 1, 0),
    ):
        if _is_walkable(game_state, px + dx, py + dy):
            legal.append(action)
    return legal


def greedy_boss_ally_turn(game_state: dict[str, Any], rng: random.Random) -> Action:
    del rng
    my_hp = int(game_state.get("my_hp", 0))
    if my_hp < 2:
        return Action.HEAL_SELF
    if _is_boss_adjacent(game_state):
        return Action.ATTACK

    position = game_state["position"]
    action = _move_toward(position, _boss_position(game_state))
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

    legal = _legal_moves(game_state)
    return legal[0] if legal else Action.WAIT


def dumb_boss_ally_turn(game_state: dict[str, Any], rng: random.Random) -> Action:
    my_hp = int(game_state.get("my_hp", 0))
    if my_hp < 2 and rng.random() < 0.4:
        return Action.HEAL_SELF
    if _is_boss_adjacent(game_state) and rng.random() < 0.35:
        return Action.ATTACK

    if rng.random() < 0.35:
        return Action.WAIT

    legal = _legal_moves(game_state)
    return rng.choice(legal) if legal else Action.WAIT
