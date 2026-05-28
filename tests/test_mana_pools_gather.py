"""Test GATHER action: adjacent gather increases energy; non-adjacent is no-op."""

from engine.core.action import Action
from engine.simulation.map import TileType
from scenarios.mana_pools.game import ManaPoolsScenario


def _setup_with_manual_positions() -> ManaPoolsScenario:
    """Create a scenario with known positions for deterministic tests."""
    s = ManaPoolsScenario(seed=1, player_ids=["p1", "p2"])
    s.setup()
    return s


def _place_bot_adjacent_to_station(s: ManaPoolsScenario, pid: str) -> tuple[int, int]:
    """Move a bot to a cell adjacent to the first station. Returns station position."""
    assert s._map is not None
    for (sx, sy) in s._pool_capacities:
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            cx, cy = sx + dx, sy + dy
            if (
                s._map.in_bounds(cx, cy)
                and s._map.get_tile(cx, cy) is TileType.EMPTY
                and (cx, cy) not in s._positions.values()
            ):
                s._positions[pid] = (cx, cy)
                return sx, sy
    raise RuntimeError("No adjacent cell found for bot")


def test_gather_adjacent_increases_energy():
    s = _setup_with_manual_positions()
    pid = "p1"
    _place_bot_adjacent_to_station(s, pid)
    initial_energy = s._energy[pid]
    initial_caps = dict(s._pool_capacities)

    actions = {p: Action.WAIT for p in s.player_ids()}
    actions[pid] = Action.GATHER
    s.apply_turn(actions)

    # Energy increased by gather_rate
    assert s._energy[pid] == initial_energy + s._gather_rate

    # Station capacity decreased by gather_rate
    for pos, cap in initial_caps.items():
        if (cap - s._gather_rate) > 0 or pos not in s._pool_capacities:
            pass
    # At least one pool decreased in capacity
    total_before = sum(initial_caps.values())
    total_after = sum(s._pool_capacities.values())
    assert total_after == total_before - s._gather_rate


def test_gather_non_adjacent_is_noop():
    s = _setup_with_manual_positions()
    pid = "p1"
    assert s._map is not None
    # Place bot far from any pool
    for y in range(s._map.height):
        for x in range(s._map.width):
            if (
                s._map.get_tile(x, y) is TileType.EMPTY
                and (x, y) not in s._positions.values()
                and not any(
                    abs(x - sx) + abs(y - sy) == 1
                    for sx, sy in s._pool_capacities
                )
            ):
                s._positions[pid] = (x, y)
                break
        else:
            continue
        break

    initial_energy = s._energy[pid]
    total_before = sum(s._pool_capacities.values())

    actions = {p: Action.WAIT for p in s.player_ids()}
    actions[pid] = Action.GATHER
    s.apply_turn(actions)

    # Energy unchanged; no station capacity spent
    assert s._energy[pid] == initial_energy
    assert sum(s._pool_capacities.values()) == total_before


def test_gather_respects_max_energy():
    s = _setup_with_manual_positions()
    pid = "p1"
    _place_bot_adjacent_to_station(s, pid)
    s._energy[pid] = s._max_energy - 2  # almost full

    actions = {p: Action.WAIT for p in s.player_ids()}
    actions[pid] = Action.GATHER
    s.apply_turn(actions)

    assert s._energy[pid] <= s._max_energy


def test_gather_increments_gathers_counter():
    s = _setup_with_manual_positions()
    pid = "p1"
    _place_bot_adjacent_to_station(s, pid)
    before = s._gathers[pid]

    actions = {p: Action.WAIT for p in s.player_ids()}
    actions[pid] = Action.GATHER
    s.apply_turn(actions)

    assert s._gathers[pid] == before + 1
