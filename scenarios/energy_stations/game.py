"""Energy Stations scenario — competitive PvP on a 16×16 grid."""

from __future__ import annotations

import random
import tomllib
from pathlib import Path
from typing import Any

from engine.core.action import Action
from engine.core.scenario import ScenarioBase
from engine.core.turn_result import TurnResult
from engine.simulation.map import Map, TileType

SCENARIO_DIR = Path(__file__).resolve().parent
MOVE_DELTAS = {
    Action.MOVE_UP: (0, -1),
    Action.MOVE_DOWN: (0, 1),
    Action.MOVE_LEFT: (-1, 0),
    Action.MOVE_RIGHT: (1, 0),
}
ORTHOGONAL_DELTAS = [(0, -1), (0, 1), (-1, 0), (1, 0)]


class EnergyStationsScenario(ScenarioBase):
    """Competitive PvP: gather energy from stations; push rivals away with ATTACK."""

    NEEDS_EXTERNAL_OPPONENT = False

    def __init__(
        self,
        seed: int,
        max_turns: int | None = None,
        *,
        player_ids: list[str] | None = None,
    ) -> None:
        self._seed = seed
        self._rng = random.Random(seed)
        cfg = self._load_config()
        self._cfg = cfg

        sc = cfg["scenario"]
        self._map_width = int(sc["map_width"])
        self._map_height = int(sc["map_height"])
        self._station_count = int(sc["station_count"])
        self._obstacle_count = int(sc["obstacle_count"])
        self._max_turns = max_turns if max_turns is not None else int(sc["max_turns"])
        self._min_players = int(sc.get("min_players", 2))
        self._max_players = int(sc.get("max_players", 8))

        pc = cfg["player"]
        self._starting_energy = int(pc["starting_energy"])
        self._max_energy = int(pc["max_energy"])
        self._move_cost = int(pc["move_cost"])
        self._attack_cost = int(pc["attack_cost"])
        self._gather_rate = int(pc["gather_rate"])

        self._initial_capacity = int(cfg["station"]["initial_capacity"])

        if player_ids is None:
            self._player_ids: list[str] = ["p1", "p2"]
        else:
            cleaned = list(player_ids)
            if len(cleaned) < self._min_players or len(cleaned) > self._max_players:
                raise ValueError(
                    f"Energy Stations supports {self._min_players}–{self._max_players} players; "
                    f"got {len(cleaned)}"
                )
            if len(set(cleaned)) != len(cleaned):
                raise ValueError("Duplicate player_id in Energy Stations setup")
            self._player_ids = cleaned

        # State initialised in setup()
        self._map: Map | None = None
        self._positions: dict[str, tuple[int, int]] = {}
        self._energy: dict[str, int] = {}
        # (x, y) -> remaining_capacity
        self._station_capacities: dict[tuple[int, int], int] = {}
        self._turn = 0
        self._finished = False

        # Per-bot stats for scoring/metrics
        self._gathers: dict[str, int] = {pid: 0 for pid in self._player_ids}
        self._pushes_landed: dict[str, int] = {pid: 0 for pid in self._player_ids}
        self._pushes_blocked: dict[str, int] = {pid: 0 for pid in self._player_ids}
        self._moves: dict[str, int] = {pid: 0 for pid in self._player_ids}

    @staticmethod
    def _load_config() -> dict[str, Any]:
        with (SCENARIO_DIR / "scenario.toml").open("rb") as fh:
            return tomllib.load(fh)

    @classmethod
    def player_limits(cls) -> tuple[int, int]:
        cfg = cls._load_config()
        return int(cfg["scenario"].get("min_players", 2)), int(cfg["scenario"].get("max_players", 8))

    def player_ids(self) -> list[str]:
        return list(self._player_ids)

    def positions_snapshot(self) -> dict[str, tuple[int, int]]:
        return dict(self._positions)

    # ── Setup ─────────────────────────────────────────────────────────────────

    def setup(self) -> None:
        self._map = Map(self._map_width, self._map_height)
        self._station_capacities = {}

        self._place_obstacles(self._obstacle_count)
        self._place_stations(self._station_count)
        self._place_players()

        self._gathers = {pid: 0 for pid in self._player_ids}
        self._pushes_landed = {pid: 0 for pid in self._player_ids}
        self._pushes_blocked = {pid: 0 for pid in self._player_ids}
        self._moves = {pid: 0 for pid in self._player_ids}
        self._turn = 0
        self._finished = False

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

    def _place_stations(self, count: int) -> None:
        assert self._map is not None
        placed = 0
        attempts = 0
        while placed < count and attempts < count * 30:
            attempts += 1
            x = self._rng.randint(1, self._map.width - 2)
            y = self._rng.randint(1, self._map.height - 2)
            if self._map.get_tile(x, y) != TileType.EMPTY:
                continue
            self._map.set_tile(x, y, TileType.STATION)
            self._station_capacities[(x, y)] = self._initial_capacity
            placed += 1

    def _place_players(self) -> None:
        assert self._map is not None
        self._positions = {}
        self._energy = {}
        n = len(self._player_ids)
        if n == 0:
            return

        # Spread bots around the outer ring for minimum separation
        border = self._border_cells()
        step = max(1, len(border) // n)
        for i, pid in enumerate(self._player_ids):
            # Find next available border cell with minimum separation
            for offset in range(len(border)):
                idx = (i * step + offset) % len(border)
                x, y = border[idx]
                if (x, y) not in self._positions.values():
                    self._positions[pid] = (x, y)
                    break
            else:
                # Fallback: find any empty non-station cell
                for ty in range(self._map.height):
                    for tx in range(self._map.width):
                        if (
                            self._map.get_tile(tx, ty) == TileType.EMPTY
                            and (tx, ty) not in self._positions.values()
                        ):
                            self._positions[pid] = (tx, ty)
                            break
            self._energy[pid] = self._starting_energy

    def _border_cells(self) -> list[tuple[int, int]]:
        """All walkable border cells, sorted clockwise."""
        assert self._map is not None
        w, h = self._map_width, self._map_height
        border: list[tuple[int, int]] = []
        for x in range(w):
            border.append((x, 0))
        for y in range(1, h):
            border.append((w - 1, y))
        for x in range(w - 2, -1, -1):
            border.append((x, h - 1))
        for y in range(h - 2, 0, -1):
            border.append((0, y))
        return [
            (x, y)
            for x, y in border
            if self._map.get_tile(x, y) == TileType.EMPTY
        ]

    # ── Turn resolution ────────────────────────────────────────────────────────

    def apply_turn(self, actions: dict[str, Action]) -> TurnResult:
        assert self._map is not None
        self._turn += 1
        events: list[str] = []

        # Resolve actions in sorted player_id order for determinism
        for pid in sorted(self._player_ids):
            action = actions.get(pid, Action.WAIT)
            events.extend(self._apply_player_action(pid, action))

        # Check win conditions
        if not self._station_capacities:
            self._finished = True
            events.append("all_stations_depleted")

        scores = self.calculate_score()
        return TurnResult(
            turn_number=self._turn,
            actions=actions,
            scores=scores,
            events=events,
        )

    def _apply_player_action(self, pid: str, action: Action) -> list[str]:
        assert self._map is not None
        events: list[str] = []
        x, y = self._positions[pid]

        if action in MOVE_DELTAS:
            dx, dy = MOVE_DELTAS[action]
            nx, ny = x + dx, y + dy
            if self._can_move_to(nx, ny, exclude_pid=pid):
                # Deduct move cost (floor at 0)
                self._energy[pid] = max(0, self._energy[pid] - self._move_cost)
                self._positions[pid] = (nx, ny)
                self._moves[pid] += 1
                events.append(f"{pid}_moved")
            else:
                events.append(f"{pid}_blocked")

        elif action is Action.GATHER:
            adjacent = self._adjacent_stations(x, y)
            if adjacent:
                # Pick station with most remaining capacity (deterministic: sort by coord)
                sx, sy = max(
                    adjacent,
                    key=lambda pos: (self._station_capacities.get(pos, 0), pos),
                )
                cap = self._station_capacities.get((sx, sy), 0)
                if cap > 0:
                    gained = min(self._gather_rate, cap)
                    # Apply cap
                    gained = min(gained, self._max_energy - self._energy[pid])
                    self._energy[pid] = min(self._max_energy, self._energy[pid] + gained)
                    self._station_capacities[(sx, sy)] -= gained
                    self._gathers[pid] += 1
                    events.append(f"{pid}_gathered_{gained}")
                    # Deplete station if empty
                    if self._station_capacities[(sx, sy)] <= 0:
                        del self._station_capacities[(sx, sy)]
                        self._map.set_tile(sx, sy, TileType.EMPTY)
                        events.append(f"station_{sx}_{sy}_depleted")
                else:
                    events.append(f"{pid}_gather_failed_no_capacity")
            else:
                events.append(f"{pid}_gather_failed_not_adjacent")

        elif action is Action.ATTACK:
            current_energy = self._energy[pid]
            if current_energy == 0:
                # No energy: silently treat as WAIT
                events.append(f"{pid}_attack_no_energy")
                return events

            # Find all adjacent bots (sorted by player_id for determinism)
            adjacent_bots = self._adjacent_bots(x, y, exclude_pid=pid)
            if not adjacent_bots:
                events.append(f"{pid}_attack_no_target")
                return events

            # Auto-target: bot with lowest player_id
            target_pid = min(adjacent_bots)
            tx, ty = self._positions[target_pid]

            # Direction of push: from attacker toward target
            pdx = tx - x
            pdy = ty - y

            # Destination after push
            dest_x = tx + pdx
            dest_y = ty + pdy

            # Deduct attack cost
            self._energy[pid] = max(0, self._energy[pid] - self._attack_cost)

            if self._can_move_to(dest_x, dest_y, exclude_pid=target_pid):
                self._positions[target_pid] = (dest_x, dest_y)
                self._pushes_landed[pid] += 1
                events.append(f"{pid}_pushed_{target_pid}")
            else:
                self._pushes_blocked[pid] += 1
                events.append(f"{pid}_push_blocked_{target_pid}")

        elif action is Action.WAIT:
            events.append(f"{pid}_waited")

        else:
            # Unknown action treated as WAIT
            events.append(f"{pid}_waited")

        return events

    def _can_move_to(self, x: int, y: int, *, exclude_pid: str) -> bool:
        assert self._map is not None
        if not self._map.in_bounds(x, y):
            return False
        tile = self._map.get_tile(x, y)
        if tile is TileType.OBSTACLE or tile is TileType.STATION:
            return False
        for other_pid, (ox, oy) in self._positions.items():
            if other_pid != exclude_pid and ox == x and oy == y:
                return False
        return True

    def _adjacent_stations(self, x: int, y: int) -> list[tuple[int, int]]:
        """Stations orthogonally adjacent to (x, y) with remaining capacity."""
        assert self._map is not None
        result = []
        for dx, dy in ORTHOGONAL_DELTAS:
            nx, ny = x + dx, y + dy
            if (
                self._map.in_bounds(nx, ny)
                and self._map.get_tile(nx, ny) is TileType.STATION
                and self._station_capacities.get((nx, ny), 0) > 0
            ):
                result.append((nx, ny))
        return result

    def _adjacent_bots(self, x: int, y: int, *, exclude_pid: str) -> list[str]:
        """Player IDs of bots orthogonally adjacent to (x, y), excluding self."""
        result = []
        for dx, dy in ORTHOGONAL_DELTAS:
            nx, ny = x + dx, y + dy
            for pid, (px, py) in self._positions.items():
                if pid != exclude_pid and px == nx and py == ny:
                    result.append(pid)
        return result

    # ── Scoring ────────────────────────────────────────────────────────────────

    def calculate_score(self) -> dict[str, int]:
        if not self._energy:
            return {pid: 0 for pid in self._player_ids}
        max_e = max(self._energy.values()) or 1
        return {
            pid: round(self._energy[pid] / max_e * 100)
            for pid in self._player_ids
        }

    def is_finished(self) -> bool:
        if self._finished:
            return True
        if self._turn >= self._max_turns:
            return True
        return False

    # ── State for student API ──────────────────────────────────────────────────

    def build_game_state(self, player_id: str) -> dict[str, Any]:
        assert self._map is not None
        x, y = self._positions[player_id]
        visible_tiles = [
            {"x": tx, "y": ty, "type": tile.value}
            for tx, ty, tile in self._map.iter_tiles()
        ]
        others: dict[str, list[int]] = {
            oid: list(self._positions[oid])
            for oid in self._player_ids
            if oid != player_id
        }
        stations_list = [
            {"x": sx, "y": sy, "capacity": cap}
            for (sx, sy), cap in sorted(self._station_capacities.items())
        ]
        adj_stations = [
            {"x": sx, "y": sy, "capacity": self._station_capacities[(sx, sy)]}
            for sx, sy in self._adjacent_stations(x, y)
        ]
        # opponent_position: nearest other player (or self if alone)
        others_list = [
            (oid, ox, oy)
            for oid, (ox, oy) in self._positions.items()
            if oid != player_id
        ]
        if others_list:
            nearest = min(others_list, key=lambda t: abs(t[1] - x) + abs(t[2] - y))
            opp_pos = [nearest[1], nearest[2]]
        else:
            opp_pos = [x, y]

        return {
            "turn": self._turn,
            "player_id": player_id,
            "position": [x, y],
            "resources": self._energy[player_id],
            "on_resource": False,
            "map_width": self._map_width,
            "map_height": self._map_height,
            "visible_tiles": visible_tiles,
            "others": others,
            "opponent_position": opp_pos,
            # energy_stations extras
            "my_energy": self._energy[player_id],
            "max_energy": self._max_energy,
            "stations": stations_list,
            "adjacent_stations": adj_stations,
        }

    # ── Render extras for UI ───────────────────────────────────────────────────

    def render_extras(self) -> dict[str, Any]:
        """Extra render data consumed by build_render_state."""
        return {
            "energy_bars": {
                pid: {
                    "energy": self._energy.get(pid, 0),
                    "max_energy": self._max_energy,
                }
                for pid in self._player_ids
            },
            "station_capacities": {
                f"{sx},{sy}": cap
                for (sx, sy), cap in self._station_capacities.items()
            },
            "station_max_capacity": self._initial_capacity,
        }

    # ── Extra metrics for analysis pipeline ───────────────────────────────────

    def energy_metrics(self) -> dict[str, Any]:
        return {
            "energy_final": dict(self._energy),
            "gathers": dict(self._gathers),
            "pushes_landed": dict(self._pushes_landed),
            "pushes_blocked": dict(self._pushes_blocked),
            "moves": dict(self._moves),
        }
