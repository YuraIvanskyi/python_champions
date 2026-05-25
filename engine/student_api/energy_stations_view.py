"""Extended GameView for the Mana Pools scenario."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from engine.student_api.view import GameView


class EnergyStationsView(GameView):
    """Readonly state snapshot for one bot in the Mana Pools scenario.

    Extends GameView with mana and pool methods.
    """

    __slots__ = (
        "_adjacent_stations",
        "_max_energy",
        "_my_energy",
        "_stations",
    )

    def __init__(self, data: Mapping[str, Any]) -> None:
        super().__init__(data)
        self._my_energy = int(data.get("my_energy", 0))
        self._max_energy = int(data.get("max_energy", 150))

        raw_stations = data.get("stations", [])
        self._stations: list[tuple[int, int, int]] = []
        if isinstance(raw_stations, list):
            for s in raw_stations:
                if isinstance(s, dict):
                    self._stations.append((int(s["x"]), int(s["y"]), int(s["capacity"])))

        raw_adj = data.get("adjacent_stations", [])
        self._adjacent_stations: list[tuple[int, int, int]] = []
        if isinstance(raw_adj, list):
            for s in raw_adj:
                if isinstance(s, dict):
                    self._adjacent_stations.append(
                        (int(s["x"]), int(s["y"]), int(s["capacity"]))
                    )

    # ── Mana ───────────────────────────────────────────────────────────────────

    def my_energy(self) -> int:
        """Current mana level."""
        return self._my_energy

    def max_energy(self) -> int:
        """Maximum mana cap."""
        return self._max_energy

    # ── Pools ──────────────────────────────────────────────────────────────────

    def stations(self) -> list[tuple[int, int, int]]:
        """All remaining pools as list of (x, y, capacity)."""
        return list(self._stations)

    def adjacent_stations(self) -> list[tuple[int, int, int]]:
        """Pools the bot can currently gather from: (x, y, capacity)."""
        return list(self._adjacent_stations)

    def can_gather(self) -> bool:
        """True if any orthogonally adjacent pool has capacity > 0."""
        return bool(self._adjacent_stations)

    def nearest_station(self) -> tuple[int, int] | None:
        """(x, y) of the closest pool by Manhattan distance, or None."""
        if not self._stations:
            return None
        x, y = self._x, self._y
        return min(
            ((sx, sy) for sx, sy, _ in self._stations),
            key=lambda pos: abs(pos[0] - x) + abs(pos[1] - y),
        )
