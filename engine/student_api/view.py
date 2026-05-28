"""Readonly game view passed to student make_turn — use methods, not dict keys."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class TileKind:
    """Tile type strings for all scenarios."""

    EMPTY = "empty"
    RESOURCE = "resource"
    OBSTACLE = "obstacle"
    POOL = "pool"


class GameView:
    """Simplified, readonly snapshot for one bot's turn.

    Scenarios still serialize to JSON dicts for the sandbox; the engine wraps
    that payload in ``GameView`` before calling ``make_turn``.
    """

    __slots__ = (
        "_height",
        "_on_resource",
        "_opp_x",
        "_opp_y",
        "_others",
        "_player_id",
        "_score",
        "_tiles",
        "_turn",
        "_width",
        "_x",
        "_y",
    )

    def __init__(self, data: Mapping[str, Any]) -> None:
        self._turn = int(data.get("turn", 0))
        self._player_id = str(data.get("player_id", "student"))
        position = data["position"]
        self._x = int(position[0])
        self._y = int(position[1])
        self._score = int(data.get("resources", 0))
        self._on_resource = bool(data.get("on_resource", False))
        self._width = int(data["map_width"])
        self._height = int(data["map_height"])
        opponent = data.get("opponent_position", [0, 0])
        self._opp_x = int(opponent[0])
        self._opp_y = int(opponent[1])
        others_raw = data.get("others")
        if isinstance(others_raw, dict):
            self._others: dict[str, tuple[int, int]] = {
                str(k): (int(v[0]), int(v[1])) for k, v in others_raw.items()
            }
        else:
            self._others = {}
        self._tiles: dict[tuple[int, int], str] = {}
        for tile in data.get("visible_tiles", ()):
            self._tiles[(int(tile["x"]), int(tile["y"]))] = str(tile["type"])

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GameView:
        if "boss_position" in data:
            from engine.student_api.boss_fight_view import BossFightView

            return BossFightView(data)
        if "pools" in data or "stations" in data:
            from engine.student_api.mana_pools_view import ManaPoolsView

            return ManaPoolsView(data)
        return cls(data)

    def turn(self) -> int:
        return self._turn

    def player_id(self) -> str:
        return self._player_id

    def my_x(self) -> int:
        return self._x

    def my_y(self) -> int:
        return self._y

    def position(self) -> tuple[int, int]:
        return self._x, self._y

    def score(self) -> int:
        """Collected resources (gameplay score so far)."""
        return self._score

    def on_resource(self) -> bool:
        return self._on_resource

    def map_width(self) -> int:
        return self._width

    def map_height(self) -> int:
        return self._height

    def opponent_x(self) -> int:
        return self._opp_x

    def opponent_y(self) -> int:
        return self._opp_y

    def opponent_position(self) -> tuple[int, int]:
        return self._opp_x, self._opp_y

    def others_positions(self) -> list[tuple[str, int, int]]:
        """Other players' positions: (player_id, x, y) sorted by id."""
        return [
            (pid, xy[0], xy[1])
            for pid, xy in sorted(self._others.items(), key=lambda item: item[0])
        ]

    def other_units(self) -> dict[str, tuple[int, int]]:
        """Readonly map of other player_id -> (x, y)."""
        return dict(self._others)

    def position_of(self, player_id: str) -> tuple[int, int] | None:
        """Position of another player, or None if missing."""
        return self._others.get(player_id)

    def is_inside(self, x: int, y: int) -> bool:
        return 0 <= x < self._width and 0 <= y < self._height

    def tile_at(self, x: int, y: int) -> str | None:
        """Tile type at (x, y), or None if off-map or not in visible data."""
        if not self.is_inside(x, y):
            return None
        return self._tiles.get((x, y))

    def is_obstacle(self, x: int, y: int) -> bool:
        return self.tile_at(x, y) == TileKind.OBSTACLE

    def is_walkable(self, x: int, y: int) -> bool:
        if not self.is_inside(x, y):
            return False
        tile = self.tile_at(x, y)
        if tile is None:
            return False
        return tile != TileKind.OBSTACLE

    def has_resource_at(self, x: int, y: int) -> bool:
        return self.tile_at(x, y) == TileKind.RESOURCE

    def resource_tiles(self) -> list[tuple[int, int]]:
        return [(x, y) for (x, y), kind in self._tiles.items() if kind == TileKind.RESOURCE]

