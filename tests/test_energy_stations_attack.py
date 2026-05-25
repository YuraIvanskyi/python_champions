"""Test ATTACK push semantics: pushes target; blocked push costs energy but target stays."""

from engine.core.action import Action
from engine.simulation.map import TileType
from scenarios.energy_stations.game import EnergyStationsScenario


def _make_clear_scenario() -> EnergyStationsScenario:
    s = EnergyStationsScenario(seed=7, player_ids=["p1", "p2"])
    s.setup()
    assert s._map is not None
    return s


def _clear_area(s: EnergyStationsScenario, x: int, y: int, radius: int = 3) -> None:
    assert s._map is not None
    for ty in range(max(0, y - radius), min(s._map.height, y + radius + 1)):
        for tx in range(max(0, x - radius), min(s._map.width, x + radius + 1)):
            if s._map.get_tile(tx, ty) is TileType.OBSTACLE:
                s._map.set_tile(tx, ty, TileType.EMPTY)
            if s._map.get_tile(tx, ty) is TileType.STATION:
                s._map.set_tile(tx, ty, TileType.EMPTY)
                s._station_capacities.pop((tx, ty), None)


def test_attack_pushes_target_one_cell():
    s = _make_clear_scenario()
    # Set up: p1 at (5,5), p2 at (6,5) → p1 attacks p2, push is to (7,5)
    _clear_area(s, 5, 5, 4)
    s._positions["p1"] = (5, 5)
    s._positions["p2"] = (6, 5)
    energy_before = s._energy["p1"]

    actions = {"p1": Action.ATTACK, "p2": Action.WAIT}
    s.apply_turn(actions)

    # p2 pushed to (7,5)
    assert s._positions["p2"] == (7, 5)
    assert s._pushes_landed["p1"] == 1
    # attack cost deducted
    assert s._energy["p1"] == energy_before - s._attack_cost


def test_attack_push_blocked_by_wall_costs_energy():
    s = _make_clear_scenario()
    # p1 at (1,1), p2 at (1,0) → push direction is (0,-1) → dest (1,-1) out of bounds
    _clear_area(s, 1, 1, 3)
    s._positions["p1"] = (1, 1)
    s._positions["p2"] = (1, 0)
    energy_before = s._energy["p1"]

    actions = {"p1": Action.ATTACK, "p2": Action.WAIT}
    s.apply_turn(actions)

    # p2 stays at (1,0) — push blocked by wall
    assert s._positions["p2"] == (1, 0)
    assert s._pushes_blocked["p1"] == 1
    # energy still spent
    assert s._energy["p1"] == energy_before - s._attack_cost


def test_attack_push_blocked_by_obstacle():
    s = _make_clear_scenario()
    assert s._map is not None
    _clear_area(s, 4, 4, 4)
    # Place obstacle at push destination (6,4)
    s._map.set_tile(6, 4, TileType.OBSTACLE)
    s._positions["p1"] = (4, 4)
    s._positions["p2"] = (5, 4)
    energy_before = s._energy["p1"]

    actions = {"p1": Action.ATTACK, "p2": Action.WAIT}
    s.apply_turn(actions)

    assert s._positions["p2"] == (5, 4)  # unmoved
    assert s._pushes_blocked["p1"] == 1
    assert s._energy["p1"] == energy_before - s._attack_cost


def test_attack_no_energy_is_noop():
    s = _make_clear_scenario()
    _clear_area(s, 3, 3, 4)
    s._positions["p1"] = (3, 3)
    s._positions["p2"] = (4, 3)
    s._energy["p1"] = 0  # zero energy

    actions = {"p1": Action.ATTACK, "p2": Action.WAIT}
    s.apply_turn(actions)

    # No movement, no energy deducted, no push recorded
    assert s._positions["p2"] == (4, 3)
    assert s._pushes_landed["p1"] == 0
    assert s._energy["p1"] == 0


def test_attack_no_adjacent_target_is_noop():
    s = _make_clear_scenario()
    _clear_area(s, 2, 2, 5)
    s._positions["p1"] = (2, 2)
    s._positions["p2"] = (8, 8)  # far away
    energy_before = s._energy["p1"]

    actions = {"p1": Action.ATTACK, "p2": Action.WAIT}
    s.apply_turn(actions)

    assert s._pushes_landed["p1"] == 0
    assert s._pushes_blocked["p1"] == 0
    assert s._energy["p1"] == energy_before  # no cost for no-target attack
