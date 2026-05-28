"""Resource Wars scenario implementation."""

from __future__ import annotations

import random
from typing import Any

from engine.core.action import Action
from engine.core.scenario import ScenarioBase
from engine.core.scenario_config import load_scenario_section
from engine.core.turn_result import TurnResult
from engine.simulation.entity import Entity
from engine.simulation.map import Map, TileType

MOVE_DELTAS = {
    Action.MOVE_UP: (0, -1),
    Action.MOVE_DOWN: (0, 1),
    Action.MOVE_LEFT: (-1, 0),
    Action.MOVE_RIGHT: (1, 0),
}


class ResourceWarsScenario(ScenarioBase):
    def __init__(
        self,
        seed: int,
        max_turns: int | None = None,
        *,
        player_ids: list[str] | None = None,
    ) -> None:
        self._seed = seed
        self._rng = random.Random(seed)
        self._config = self._load_config()
        if max_turns is not None:
            self._max_turns = max_turns
        else:
            self._max_turns = int(self._config["max_turns"])

        self._score_threshold = int(self._config["score_threshold"])
        self._min_players = int(self._config.get("min_players", 2))
        self._max_players = int(self._config.get("max_players", 8))

        if player_ids is None:
            self._player_ids = ["student", "opponent"]
        else:
            cleaned = list(player_ids)
            if len(cleaned) < self._min_players or len(cleaned) > self._max_players:
                raise ValueError(
                    f"Resource Wars supports {self._min_players}–{self._max_players} players; "
                    f"got {len(cleaned)}"
                )
            if len(set(cleaned)) != len(cleaned):
                raise ValueError("Duplicate player_id in Resource Wars setup")
            self._player_ids = cleaned

        self._map: Map | None = None
        self._entities: dict[str, Entity] = {}
        self._scores: dict[str, int] = {pid: 0 for pid in self._player_ids}
        self._turn = 0

    @staticmethod
    def _load_config() -> dict[str, Any]:
        return load_scenario_section("resource_wars")

    @classmethod
    def player_limits(cls) -> tuple[int, int]:
        cfg = cls._load_config()
        return int(cfg.get("min_players", 2)), int(cfg.get("max_players", 8))

    def player_ids(self) -> list[str]:
        """Stable order: input order from setup (file / CLI order)."""
        return list(self._player_ids)

    def positions_snapshot(self) -> dict[str, tuple[int, int]]:
        assert self._entities
        return {pid: (entity.x, entity.y) for pid, entity in self._entities.items()}

    def setup(self) -> None:
        width = int(self._config["map_width"])
        height = int(self._config["map_height"])
        self._map = Map(width, height)
        self._place_obstacles(int(self._config["obstacle_count"]))
        self._place_resources(int(self._config["resource_count"]))
        self._scores = {pid: 0 for pid in self._player_ids}

        if self._player_ids == ["student", "opponent"]:
            self._entities = {
                "student": Entity("student_unit", "student", 0, 0),
                "opponent": Entity("opponent_unit", "opponent", width - 1, height - 1),
            }
            return

        positions = self._spawn_positions_free_cells(len(self._player_ids), width, height)
        self._entities = {}
        for player_id, (sx, sy) in zip(self._player_ids, positions, strict=True):
            suffix = player_id.replace("-", "_")
            self._entities[player_id] = Entity(f"unit_{suffix}", player_id, sx, sy)

    def _spawn_positions_free_cells(
        self,
        count: int,
        width: int,
        height: int,
    ) -> list[tuple[int, int]]:
        """Deterministic empty cells (no obstacle, no resource) for N players."""
        assert self._map is not None
        candidates: list[tuple[int, int]] = []
        for y in range(height):
            for x in range(width):
                if self._map.get_tile(x, y) is TileType.EMPTY:
                    candidates.append((x, y))
        # Spread starts: sort by (x+y, x) then take evenly spaced indices in a deterministic way
        candidates.sort(key=lambda p: (p[0] + p[1], p[0]))
        if len(candidates) < count:
            raise ValueError(
                f"Not enough empty tiles for {count} players "
                f"(only {len(candidates)} on this map)"
            )
        if count == 1:
            return [candidates[0]]
        step = max(1, (len(candidates) - 1) // (count - 1))
        picks: list[tuple[int, int]] = []
        idx = 0
        for _ in range(count):
            picks.append(candidates[min(idx, len(candidates) - 1)])
            idx += step
        return picks

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
        missing = set(self._player_ids) - set(actions)
        if missing:
            raise KeyError(f"Missing actions for players: {sorted(missing)}")

        for player_id in sorted(actions.keys()):
            action = actions[player_id]
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
        others: dict[str, list[int]] = {
            oid: [self._entities[oid].x, self._entities[oid].y]
            for oid in self._player_ids
            if oid != player_id
        }
        other_ids_sorted = sorted(others.keys())
        if len(other_ids_sorted) == 1:
            lone = other_ids_sorted[0]
            opponent_position = others[lone]
        elif other_ids_sorted:
            first = other_ids_sorted[0]
            opponent_position = others[first]
        else:
            opponent_position = [entity.x, entity.y]

        return {
            "turn": self._turn,
            "player_id": player_id,
            "position": [entity.x, entity.y],
            "resources": self._scores[player_id],
            "on_resource": on_resource,
            "map_width": self._map.width,
            "map_height": self._map.height,
            "visible_tiles": visible_tiles,
            "others": others,
            "opponent_position": opponent_position,
        }
