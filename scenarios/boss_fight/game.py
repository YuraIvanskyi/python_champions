"""Boss Fight scenario — cooperative PvE on an 8×8 grid."""

from __future__ import annotations

import random
from typing import Any

from engine.core.action import Action
from engine.core.bot_profile import char_icon_path
from engine.core.config_io import load_scenario_toml
from engine.core.scenario import ScenarioBase
from engine.core.turn_result import TurnResult
from engine.simulation.map import Map, TileType

MOVE_DELTAS = {
    Action.MOVE_UP: (0, -1),
    Action.MOVE_DOWN: (0, 1),
    Action.MOVE_LEFT: (-1, 0),
    Action.MOVE_RIGHT: (1, 0),
}

# Score cap for a loss (distinguishes from a win which can reach 100)
_LOSS_SCORE_CAP = 79


class BossFightScenario(ScenarioBase):
    """All student bots cooperate against one AI-controlled boss."""

    NEEDS_EXTERNAL_OPPONENT = False

    def __init__(
        self,
        seed: int,
        max_turns: int | None = None,
        *,
        player_ids: list[str] | None = None,
        difficulty: int | None = None,
    ) -> None:
        self._seed = seed
        self._rng = random.Random(seed)
        cfg = self._load_config()
        self._cfg = cfg

        self._map_width = int(cfg["scenario"]["map_width"])
        self._map_height = int(cfg["scenario"]["map_height"])
        self._obstacle_count = int(cfg["scenario"]["obstacle_count"])
        self._max_turns = (
            max_turns if max_turns is not None else int(cfg["scenario"]["max_turns"])
        )
        self._min_players = int(cfg["scenario"].get("min_players", 1))
        self._max_players = int(cfg["scenario"].get("max_players", 6))

        boss_cfg = cfg["boss"]
        if difficulty is None:
            self._difficulty = int(boss_cfg["difficulty"])
        else:
            if difficulty not in (1, 2, 3):
                raise ValueError("Boss Fight difficulty must be 1, 2, or 3")
            self._difficulty = difficulty
        self._boss_max_hp = int(boss_cfg["hp_per_level"][self._difficulty - 1])
        self._boss_damage = int(boss_cfg["damage_per_level"][self._difficulty - 1])
        self._multi_target = bool(boss_cfg["multi_target_at_level"][self._difficulty - 1])

        player_cfg = cfg["player"]
        self._player_max_hp = int(player_cfg["max_hp"])
        self._attack_damage = int(player_cfg["attack_damage"])
        self._heal_amount = int(player_cfg["heal_amount"])

        if player_ids is None:
            self._player_ids: list[str] = ["student"]
        else:
            cleaned = list(player_ids)
            if len(cleaned) < self._min_players or len(cleaned) > self._max_players:
                raise ValueError(
                    f"Boss Fight supports {self._min_players}–{self._max_players} players; "
                    f"got {len(cleaned)}"
                )
            if len(set(cleaned)) != len(cleaned):
                raise ValueError("Duplicate player_id in Boss Fight setup")
            self._player_ids = cleaned

        # State initialised in setup()
        self._map: Map | None = None
        self._positions: dict[str, tuple[int, int]] = {}
        self._hp: dict[str, int] = {}
        self._alive: dict[str, bool] = {}
        self._boss_x = 0
        self._boss_y = 0
        self._boss_hp = 0
        self._turn = 0
        self._finished = False

        # Per-bot combat stats (for scoring and metrics)
        self._damage_dealt: dict[str, int] = {pid: 0 for pid in self._player_ids}
        self._heals_given: dict[str, int] = {pid: 0 for pid in self._player_ids}
        self._heals_received: dict[str, int] = {pid: 0 for pid in self._player_ids}
        self._turns_alive: dict[str, int] = {pid: 0 for pid in self._player_ids}

    @staticmethod
    def _load_config() -> dict[str, Any]:
        return load_scenario_toml("boss_fight")

    @classmethod
    def player_limits(cls) -> tuple[int, int]:
        cfg = cls._load_config()
        return int(cfg["scenario"].get("min_players", 1)), int(cfg["scenario"].get("max_players", 6))

    def player_ids(self) -> list[str]:
        return list(self._player_ids)

    def positions_snapshot(self) -> dict[str, tuple[int, int]]:
        return dict(self._positions)

    # ── Setup ──────────────────────────────────────────────────────────────────

    def setup(self) -> None:
        self._map = Map(self._map_width, self._map_height)
        self._place_obstacles(self._obstacle_count)

        self._boss_x = self._map_width // 2
        self._boss_y = self._map_height // 2

        # Ensure boss cell is clear
        if self._map.get_tile(self._boss_x, self._boss_y) is TileType.OBSTACLE:
            self._map.set_tile(self._boss_x, self._boss_y, TileType.EMPTY)

        self._boss_hp = self._boss_max_hp
        self._positions = {}
        self._hp = {}
        self._alive = {}

        outer_ring = self._outer_ring_cells()
        n = len(self._player_ids)
        if n == 0:
            return

        step = max(1, len(outer_ring) // n)
        for i, pid in enumerate(self._player_ids):
            idx = (i * step) % len(outer_ring)
            x, y = outer_ring[idx]
            self._positions[pid] = (x, y)
            self._hp[pid] = self._player_max_hp
            self._alive[pid] = True

        self._damage_dealt = {pid: 0 for pid in self._player_ids}
        self._heals_given = {pid: 0 for pid in self._player_ids}
        self._heals_received = {pid: 0 for pid in self._player_ids}
        self._turns_alive = {pid: 0 for pid in self._player_ids}
        self._turn = 0
        self._finished = False

    def _place_obstacles(self, count: int) -> None:
        assert self._map is not None
        placed = 0
        attempts = 0
        boss_cx = self._map_width // 2
        boss_cy = self._map_height // 2
        while placed < count and attempts < count * 20:
            attempts += 1
            x = self._rng.randint(1, self._map.width - 2)
            y = self._rng.randint(1, self._map.height - 2)
            if x == boss_cx and y == boss_cy:
                continue
            if self._map.get_tile(x, y) != TileType.EMPTY:
                continue
            self._map.set_tile(x, y, TileType.OBSTACLE)
            placed += 1

    def _outer_ring_cells(self) -> list[tuple[int, int]]:
        """All border cells that are walkable (no obstacle), sorted clockwise."""
        assert self._map is not None
        w, h = self._map_width, self._map_height
        border: list[tuple[int, int]] = []
        # Top row L→R, right col T→B, bottom row R→L, left col B→T
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
            if self._map.get_tile(x, y) is not TileType.OBSTACLE
        ]

    # ── Turn resolution ────────────────────────────────────────────────────────

    def apply_turn(self, actions: dict[str, Action]) -> TurnResult:
        assert self._map is not None
        self._turn += 1
        events: list[str] = []

        # Count alive turns before applying (bots that survived to this turn)
        for pid in self._player_ids:
            if self._alive[pid]:
                self._turns_alive[pid] += 1

        # Student bot actions in sorted player_id order; dead bots skipped
        for pid in sorted(self._player_ids):
            if not self._alive[pid]:
                continue
            action = actions.get(pid, Action.WAIT)
            events.extend(self._apply_player_action(pid, action))

        # Boss AI
        events.extend(self._apply_boss_turn())

        # Check win/lose
        if self._boss_hp <= 0:
            self._finished = True
            events.append("boss_defeated")
        elif all(not self._alive[pid] for pid in self._player_ids):
            self._finished = True
            events.append("party_wiped")

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
            if self._can_bot_move_to(nx, ny, pid):
                self._positions[pid] = (nx, ny)
                events.append(f"{pid}_moved")
            else:
                events.append(f"{pid}_blocked")

        elif action is Action.ATTACK:
            if self._is_adjacent_to_boss(x, y):
                self._boss_hp -= self._attack_damage
                self._damage_dealt[pid] += self._attack_damage
                events.append(f"{pid}_attacked_boss")
                if self._boss_hp < 0:
                    self._boss_hp = 0
            else:
                events.append(f"{pid}_attack_wasted")

        elif action is Action.HEAL_SELF:
            old = self._hp[pid]
            self._hp[pid] = min(self._player_max_hp, self._hp[pid] + self._heal_amount)
            healed = self._hp[pid] - old
            self._heals_given[pid] += healed
            self._heals_received[pid] += healed
            events.append(f"{pid}_healed_self_{healed}")

        elif action is Action.HEAL_ALLY:
            target = self._find_weakest_ally(pid)
            if target is not None:
                old = self._hp[target]
                self._hp[target] = min(self._player_max_hp, self._hp[target] + self._heal_amount)
                healed = self._hp[target] - old
                self._heals_given[pid] += healed
                self._heals_received[target] += healed
                events.append(f"{pid}_healed_ally_{target}_{healed}")
            else:
                # No other living ally — heal self instead
                old = self._hp[pid]
                self._hp[pid] = min(self._player_max_hp, self._hp[pid] + self._heal_amount)
                healed = self._hp[pid] - old
                self._heals_given[pid] += healed
                self._heals_received[pid] += healed
                events.append(f"{pid}_healed_self_fallback_{healed}")

        elif action is Action.WAIT:
            events.append(f"{pid}_waited")
        else:
            # Unsupported action treated as WAIT
            events.append(f"{pid}_waited")

        return events

    def _can_bot_move_to(self, x: int, y: int, pid: str) -> bool:
        assert self._map is not None
        if not self._map.in_bounds(x, y):
            return False
        if self._map.get_tile(x, y) is TileType.OBSTACLE:
            return False
        if x == self._boss_x and y == self._boss_y:
            return False
        for other_id, (ox, oy) in self._positions.items():
            if other_id != pid and self._alive[other_id] and ox == x and oy == y:
                return False
        return True

    def _is_adjacent_to_boss(self, x: int, y: int) -> bool:
        return abs(x - self._boss_x) + abs(y - self._boss_y) == 1

    def _find_weakest_ally(self, pid: str) -> str | None:
        """Living ally (not self) with lowest current HP; None if no such ally exists."""
        best_id: str | None = None
        best_hp = self._player_max_hp + 1
        for other in self._player_ids:
            if other == pid or not self._alive[other]:
                continue
            if self._hp[other] < best_hp:
                best_hp = self._hp[other]
                best_id = other
        return best_id

    def _apply_boss_turn(self) -> list[str]:
        events: list[str] = []
        living = [pid for pid in self._player_ids if self._alive[pid]]
        if not living:
            return events

        # Move boss toward target
        if self._difficulty == 3:
            tx, ty = self._boss_centre_of_mass(living)
        else:
            tx, ty = self._nearest_bot_position(living)

        # One step toward target
        moved = self._boss_move_toward(tx, ty)
        if moved:
            events.append("boss_moved")

        # Attack adjacent bots
        adjacent = self._bots_adjacent_to_boss(living)
        if not adjacent:
            return events

        if self._difficulty == 1:
            targets = adjacent[:1]
        elif self._difficulty == 2:
            # Smart targeting: if multiple adjacent, pick lowest HP
            targets = [min(adjacent, key=lambda p: self._hp[p])]
        else:
            # Level 3: up to 2 adjacent bots, lowest HP first
            targets = sorted(adjacent, key=lambda p: self._hp[p])[:2]

        for pid in targets:
            self._hp[pid] -= self._boss_damage
            events.append(f"boss_attacked_{pid}")
            if self._hp[pid] <= 0:
                self._hp[pid] = 0
                self._alive[pid] = False
                events.append(f"{pid}_dead")

        return events

    def _boss_move_toward(self, tx: int, ty: int) -> bool:
        """Move boss one step toward (tx, ty); blocked by obstacles only.

        Always orthogonal (Manhattan distance): prefer the dominant axis first,
        then fall back to the other axis.
        """
        assert self._map is not None
        bx, by = self._boss_x, self._boss_y
        if bx == tx and by == ty:
            return False

        dx = 0 if bx == tx else (1 if tx > bx else -1)
        dy = 0 if by == ty else (1 if ty > by else -1)

        # Manhattan distance tells us which axis to prefer
        dist_x = abs(tx - bx)
        dist_y = abs(ty - by)

        # Try the longer-distance axis first; fall back to the other
        if dist_x >= dist_y:
            # Prefer horizontal
            candidates = [(bx + dx, by), (bx, by + dy)] if dy != 0 else [(bx + dx, by)]
        else:
            # Prefer vertical
            candidates = [(bx, by + dy), (bx + dx, by)] if dx != 0 else [(bx, by + dy)]

        for nx, ny in candidates:
            if (
                self._map.in_bounds(nx, ny)
                and self._map.get_tile(nx, ny) is not TileType.OBSTACLE
                and not self._cell_has_living_bot(nx, ny)
            ):
                self._boss_x, self._boss_y = nx, ny
                return True
        return False

    def _cell_has_living_bot(self, x: int, y: int) -> bool:
        return any(
            self._alive[pid] and self._positions[pid] == (x, y)
            for pid in self._player_ids
        )

    def _nearest_bot_position(self, living: list[str]) -> tuple[int, int]:
        bx, by = self._boss_x, self._boss_y
        return min(
            (self._positions[pid] for pid in living),
            key=lambda p: abs(p[0] - bx) + abs(p[1] - by),
        )

    def _boss_centre_of_mass(self, living: list[str]) -> tuple[int, int]:
        xs = [self._positions[pid][0] for pid in living]
        ys = [self._positions[pid][1] for pid in living]
        return round(sum(xs) / len(xs)), round(sum(ys) / len(ys))

    def _bots_adjacent_to_boss(self, living: list[str]) -> list[str]:
        return [
            pid for pid in living
            if self._is_adjacent_to_boss(*self._positions[pid])
        ]

    # ── Scoring ────────────────────────────────────────────────────────────────

    def calculate_score(self) -> dict[str, int]:
        boss_defeated = self._boss_hp <= 0
        total_damage = sum(self._damage_dealt.values()) or 1
        scores: dict[str, int] = {}
        for pid in self._player_ids:
            fraction = self._damage_dealt[pid] / total_damage
            if boss_defeated:
                scores[pid] = round(fraction * 100)
            else:
                raw = round(fraction * _LOSS_SCORE_CAP)
                scores[pid] = raw
        return scores

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
            if oid != player_id and self._alive[oid]
        }
        return {
            "turn": self._turn,
            "player_id": player_id,
            "position": [x, y],
            "resources": self.calculate_score().get(player_id, 0),
            "on_resource": False,
            "map_width": self._map_width,
            "map_height": self._map_height,
            "visible_tiles": visible_tiles,
            "others": others,
            "opponent_position": [self._boss_x, self._boss_y],
            # boss-fight extras
            "my_hp": self._hp[player_id],
            "my_max_hp": self._player_max_hp,
            "boss_position": {"x": self._boss_x, "y": self._boss_y},
            "boss_hp": self._boss_hp,
            "boss_max_hp": self._boss_max_hp,
            "boss_difficulty": self._difficulty,
            "others_hp": {
                oid: {
                    "hp": self._hp[oid],
                    "max_hp": self._player_max_hp,
                    "alive": self._alive[oid],
                }
                for oid in self._player_ids
                if oid != player_id
            },
        }

    # ── Render extras for UI ───────────────────────────────────────────────────

    def render_extras(self) -> dict[str, Any]:
        """Extra render data consumed by build_render_state."""
        return {
            "boss_entity": {
                "id": "boss",
                "position": [self._boss_x, self._boss_y],
                "display_name": "Boss",
                "hp": self._boss_hp,
                "max_hp": self._boss_max_hp,
                "is_boss": True,
                "icon": str(char_icon_path(99)),
            },
            "hp_bars": {
                pid: {
                    "hp": self._hp[pid],
                    "max_hp": self._player_max_hp,
                    "alive": self._alive[pid],
                }
                for pid in self._player_ids
            },
        }

    # ── Extra metrics for analysis pipeline ───────────────────────────────────

    def boss_metrics(self) -> dict[str, Any]:
        return {
            "boss_hp_final": self._boss_hp,
            "damage_dealt": dict(self._damage_dealt),
            "heals_given": dict(self._heals_given),
            "heals_received": dict(self._heals_received),
            "turns_alive": dict(self._turns_alive),
        }
