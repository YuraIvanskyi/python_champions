"""Grid map storage and bounds checks."""

from __future__ import annotations

from enum import StrEnum


class TileType(StrEnum):
    EMPTY = "empty"
    RESOURCE = "resource"
    OBSTACLE = "obstacle"


class Map:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self._tiles: list[list[TileType]] = [
            [TileType.EMPTY for _ in range(width)] for _ in range(height)
        ]

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_tile(self, x: int, y: int) -> TileType:
        return self._tiles[y][x]

    def set_tile(self, x: int, y: int, tile: TileType) -> None:
        if not self.in_bounds(x, y):
            raise ValueError(f"Tile ({x}, {y}) out of bounds")
        self._tiles[y][x] = tile

    def iter_tiles(self):
        for y in range(self.height):
            for x in range(self.width):
                yield x, y, self._tiles[y][x]
