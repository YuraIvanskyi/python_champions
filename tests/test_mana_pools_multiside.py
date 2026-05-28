"""Test 4 bots gathering from the same station simultaneously (N/S/E/W sides)."""

from engine.core.action import Action
from engine.simulation.map import TileType
from scenarios.mana_pools.game import ManaPoolsScenario


def _build_4side_scenario() -> tuple[ManaPoolsScenario, tuple[int, int]]:
    """Create a scenario with 4 bots placed N/S/E/W of a single station."""
    s = ManaPoolsScenario(
        seed=99,
        player_ids=["north", "south", "east", "west"],
    )
    s.setup()
    assert s._map is not None

    # Find a pool whose all 4 cardinal neighbours are empty or can be vacated
    target: tuple[int, int] | None = None
    for (sx, sy) in list(s._pool_capacities.keys()):
        candidates = [(sx, sy - 1), (sx, sy + 1), (sx + 1, sy), (sx - 1, sy)]
        if all(
            s._map.in_bounds(cx, cy) and s._map.get_tile(cx, cy) is TileType.EMPTY
            for cx, cy in candidates
        ):
            target = (sx, sy)
            break

    if target is None:
        # Fallback: place a pool and clear around it
        # Place pool at centre of map
        cx_s = s._map_width // 2
        cy_s = s._map_height // 2
        for x, y, tile in list(s._map.iter_tiles()):
            if abs(x - cx_s) <= 2 and abs(y - cy_s) <= 2:
                s._map.set_tile(x, y, TileType.EMPTY)
        s._map.set_tile(cx_s, cy_s, TileType.POOL)
        cap = s._initial_capacity
        s._pool_capacities[(cx_s, cy_s)] = cap
        target = (cx_s, cy_s)

    sx, sy = target
    s._positions["north"] = (sx, sy - 1)
    s._positions["south"] = (sx, sy + 1)
    s._positions["east"]  = (sx + 1, sy)
    s._positions["west"]  = (sx - 1, sy)
    # Reset energy to known values
    for pid in s.player_ids():
        s._energy[pid] = s._starting_energy

    return s, target


def test_four_side_simultaneous_gather():
    s, (sx, sy) = _build_4side_scenario()
    initial_cap = s._pool_capacities[(sx, sy)]
    initial_energies = {pid: s._energy[pid] for pid in s.player_ids()}

    actions = {pid: Action.GATHER for pid in s.player_ids()}
    s.apply_turn(actions)

    # Each bot should have gained gather_rate (or less if station capacity ran out)
    total_gained = sum(s._energy[pid] - initial_energies[pid] for pid in s.player_ids())
    expected_drain = min(4 * s._gather_rate, initial_cap)
    assert total_gained == expected_drain


def test_four_side_capacity_drains_correctly():
    s, (sx, sy) = _build_4side_scenario()
    initial_cap = s._pool_capacities[(sx, sy)]

    actions = {pid: Action.GATHER for pid in s.player_ids()}
    s.apply_turn(actions)

    drained = 4 * s._gather_rate
    expected_remaining = max(0, initial_cap - drained)
    if expected_remaining > 0:
        assert s._pool_capacities[(sx, sy)] == expected_remaining
    else:
        # Station should be depleted and removed
        assert (sx, sy) not in s._pool_capacities


def test_capacity_capped_per_gather_when_station_near_empty():
    """If station has only 3 energy left and 4 bots gather, total drain = 3."""
    s, (sx, sy) = _build_4side_scenario()
    # Set pool to just 3 capacity
    s._pool_capacities[(sx, sy)] = 3

    actions = {pid: Action.GATHER for pid in s.player_ids()}
    s.apply_turn(actions)

    total_gained = sum(s._energy[pid] - s._starting_energy for pid in s.player_ids())
    assert total_gained == 3
    assert (sx, sy) not in s._pool_capacities
