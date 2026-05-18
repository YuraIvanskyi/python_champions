"""Resource Wars scenario implementation."""

from __future__ import annotations

import random
import tomllib
from pathlib import Path
from typing import Any

from engine.core.action import Action
from engine.core.scenario import ScenarioBase
from engine.core.turn_result import TurnResult
from engine.simulation.entity import Entity
from engine.simulation.map import Map, TileType

SCENARIO_DIR = Path(__file__).resolve().parent
MOVE_DELTAS = {
    Action.MOVE_UP: (0, -1),
    Action.MOVE_DOWN: (0, 1),
    Action.MOVE_LEFT: (-1, 0),
    Action.MOVE_RIGHT: (1, 0),
}


class ResourceWarsScenario(ScenarioBase):
    def __init__(self, seed: int, max_turns: int | None = None) -> None:
        self._seed = seed
        self._rng = random.Random(seed)
        self._config = self._load_config()
        if max_turns is not None:
            self._max_turns = max_turns
        else:
            self._max_turns = int(self._config["max_turns"])

        self._score_threshold = int(self._config["score_threshold"])
        self._map: Map | None = None
        self._entities: dict[str, Entity] = {}
        self._scores: dict[str, int] = {"student": 0, "opponent": 0}
        self._turn = 0

    @staticmethod
    def _load_config() -> dict[str, int | str]:
        with (SCENARIO_DIR / "scenario.toml").open("rb") as handle:
            data = tomllib.load(handle)
        return data["scenario"]

    def setup(self) -> None:
        width = int(self._config["map_width"])
        height = int(self._config["map_height"])
        self._map = Map(width, height)
        self._place_obstacles(int(self._config["obstacle_count"]))
        self._place_resources(int(self._config["resource_count"]))
        self._entities = {
            "student": Entity("student_unit", "student", 0, 0),
            "opponent": Entity("opponent_unit", "opponent", width - 1, height - 1),
        }

    def _place_obstacles(self, count: int) -> None:
        assert self._map is not None
        placed = 0
        attempts = 0
        while placed < count and attempts < count * 20:
            attempts += 1
            x = self._rng.randint(1, self._map.width - 2)
            y = self._rng.randint(1, self._map.height - 2)
            if self._map.get_tile(x, y) != TileType.EMPTY:
                continue
            self._map.set_tile(x, y, TileType.OBSTACLE)
            placed += 1

    def _place_resources(self, count: int) -> None:
        assert self._map is not None
        placed = 0
        attempts = 0
        while placed < count and attempts < count * 30:
            attempts += 1
            x = self._rng.randint(0, self._map.width - 1)
            y = self._rng.randint(0, self._map.height - 1)
            if self._map.get_tile(x, y) != TileType.EMPTY:
                continue
            self._map.set_tile(x, y, TileType.RESOURCE)
            placed += 1

    def apply_turn(self, actions: dict[str, Action]) -> TurnResult:
        assert self._map is not None
        self._turn += 1
        events: list[str] = []

        for player_id, action in actions.items():
            entity = self._entities[player_id]
            if action in MOVE_DELTAS:
                dx, dy = MOVE_DELTAS[action]
                nx, ny = entity.x + dx, entity.y + dy
                if self._can_move_to(nx, ny, player_id):
                    entity.x, entity.y = nx, ny
                    events.append(f"{player_id}_moved")
                else:
                    events.append(f"{player_id}_blocked")
            elif action is Action.GATHER:
                if self._map.get_tile(entity.x, entity.y) is TileType.RESOURCE:
                    self._scores[player_id] += 1
                    self._map.set_tile(entity.x, entity.y, TileType.EMPTY)
                    events.append(f"{player_id}_gathered")
                else:
                    events.append(f"{player_id}_gather_failed")
            elif action is Action.WAIT:
                events.append(f"{player_id}_waited")

        return TurnResult(
            turn_number=self._turn,
            actions=actions,
            scores=dict(self._scores),
            events=events,
        )

    def _can_move_to(self, x: int, y: int, player_id: str) -> bool:
        assert self._map is not None
        if not self._map.in_bounds(x, y):
            return False
        if self._map.get_tile(x, y) is TileType.OBSTACLE:
            return False
        for other_id, other in self._entities.items():
            if other_id != player_id and other.x == x and other.y == y:
                return False
        return True

    def calculate_score(self) -> dict[str, int]:
        return dict(self._scores)

    def is_finished(self) -> bool:
        if self._turn >= self._max_turns:
            return True
        return any(score >= self._score_threshold for score in self._scores.values())

    def build_game_state(self, player_id: str) -> dict[str, Any]:
        assert self._map is not None
        entity = self._entities[player_id]
        on_resource = self._map.get_tile(entity.x, entity.y) is TileType.RESOURCE
        visible_tiles = [
            {"x": x, "y": y, "type": tile.value}
            for x, y, tile in self._map.iter_tiles()
        ]
        return {
            "turn": self._turn,
            "player_id": player_id,
            "position": [entity.x, entity.y],
            "resources": self._scores[player_id],
            "on_resource": on_resource,
            "map_width": self._map.width,
            "map_height": self._map.height,
            "visible_tiles": visible_tiles,
            "opponent_position": [
                self._entities["opponent" if player_id == "student" else "student"].x,
                self._entities["opponent" if player_id == "student" else "student"].y,
            ],
        }
