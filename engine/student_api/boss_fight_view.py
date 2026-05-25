"""Extended GameView for the Boss Fight scenario."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from engine.student_api.view import GameView


class BossFightView(GameView):
    """Readonly state snapshot for one bot in the Boss Fight scenario.

    Extends GameView with boss and HP methods.
    """

    __slots__ = (
        "_boss_difficulty",
        "_boss_hp",
        "_boss_max_hp",
        "_boss_x",
        "_boss_y",
        "_my_hp",
        "_my_max_hp",
        "_others_hp",
    )

    def __init__(self, data: Mapping[str, Any]) -> None:
        super().__init__(data)
        self._my_hp = int(data.get("my_hp", self._player_max_hp_fallback()))
        self._my_max_hp = int(data.get("my_max_hp", 4))
        boss_pos = data.get("boss_position", {"x": 0, "y": 0})
        self._boss_x = int(boss_pos.get("x", boss_pos[0] if isinstance(boss_pos, list) else 0))
        self._boss_y = int(boss_pos.get("y", boss_pos[1] if isinstance(boss_pos, list) else 0))
        self._boss_hp = int(data.get("boss_hp", 0))
        self._boss_max_hp = int(data.get("boss_max_hp", 1))
        self._boss_difficulty = int(data.get("boss_difficulty", 1))
        raw_others_hp = data.get("others_hp", {})
        self._others_hp: dict[str, dict[str, Any]] = {}
        if isinstance(raw_others_hp, dict):
            for pid, info in raw_others_hp.items():
                if isinstance(info, dict):
                    self._others_hp[str(pid)] = {
                        "hp": int(info.get("hp", 0)),
                        "max_hp": int(info.get("max_hp", 4)),
                        "alive": bool(info.get("alive", True)),
                    }

    def _player_max_hp_fallback(self) -> int:
        return 4

    # ── Bot HP ─────────────────────────────────────────────────────────────────

    def my_hp(self) -> int:
        """Current bot HP."""
        return self._my_hp

    def my_max_hp(self) -> int:
        """Maximum bot HP."""
        return self._my_max_hp

    def is_alive(self) -> bool:
        """Whether this bot is still alive (HP > 0)."""
        return self._my_hp > 0

    # ── Boss info ──────────────────────────────────────────────────────────────

    def boss_x(self) -> int:
        """Boss column."""
        return self._boss_x

    def boss_y(self) -> int:
        """Boss row."""
        return self._boss_y

    def boss_hp(self) -> int:
        """Current boss HP."""
        return self._boss_hp

    def boss_max_hp(self) -> int:
        """Maximum boss HP."""
        return self._boss_max_hp

    def is_boss_adjacent(self) -> bool:
        """True when the boss is orthogonally adjacent to this bot."""
        return abs(self._x - self._boss_x) + abs(self._y - self._boss_y) == 1

    # ── Ally HP ────────────────────────────────────────────────────────────────

    def ally_hp(self, player_id: str) -> int | None:
        """Current HP of a named ally, or None if not found."""
        info = self._others_hp.get(player_id)
        if info is None:
            return None
        return info["hp"]

    def weakest_ally_id(self) -> str | None:
        """player_id of the living ally with the lowest current HP, or None."""
        best_id: str | None = None
        best_hp = self._my_max_hp + 1
        for pid, info in self._others_hp.items():
            if info["alive"] and info["hp"] < best_hp:
                best_hp = info["hp"]
                best_id = pid
        return best_id
