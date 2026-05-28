"""Test MOVE actions: obstructed moves still cost energy."""

from engine.core.action import Action
from engine.simulation.map import TileType
from scenarios.mana_pools.game import ManaPoolsScenario


def _make_clear_scenario() -> ManaPoolsScenario:
    s = ManaPoolsScenario(seed=7, player_ids=["p1", "p2"])
    s.setup()
    assert s._map is not None
    return s


def _clear_area(s: ManaPoolsScenario, x: int, y: int, radius: int = 3) -> None:
    assert s._map is not None
    for ty in range(max(0, y - radius), min(s._map.height, y + radius + 1)):
        for tx in range(max(0, x - radius), min(s._map.width, x + radius + 1)):
            if s._map.get_tile(tx, ty) is TileType.OBSTACLE:
                s._map.set_tile(tx, ty, TileType.EMPTY)
            if s._map.get_tile(tx, ty) is TileType.POOL:
                s._map.set_tile(tx, ty, TileType.EMPTY)
                s._pool_capacities.pop((tx, ty), None)


def test_move_success_costs_energy():
    s = _make_clear_scenario()
    _clear_area(s, 5, 5, 4)
    s._positions["p1"] = (5, 5)
    energy_before = s._energy["p1"]

    s.apply_turn({"p1": Action.MOVE_RIGHT, "p2": Action.WAIT})

    assert s._positions["p1"] == (6, 5)
    assert s._moves["p1"] == 1
    assert s._energy["p1"] == energy_before - s._move_cost


def test_move_blocked_by_wall_costs_energy():
    s = _make_clear_scenario()
    _clear_area(s, 0, 0, 2)
    s._positions["p1"] = (0, 0)
    energy_before = s._energy["p1"]

    s.apply_turn({"p1": Action.MOVE_LEFT, "p2": Action.WAIT})

    assert s._positions["p1"] == (0, 0)
    assert s._moves["p1"] == 0
    assert s._energy["p1"] == energy_before - s._move_cost


def test_move_blocked_by_obstacle_costs_energy():
    s = _make_clear_scenario()
    _clear_area(s, 4, 4, 4)
    assert s._map is not None
    s._map.set_tile(6, 4, TileType.OBSTACLE)
    s._positions["p1"] = (5, 4)
    energy_before = s._energy["p1"]

    s.apply_turn({"p1": Action.MOVE_RIGHT, "p2": Action.WAIT})

    assert s._positions["p1"] == (5, 4)
    assert s._moves["p1"] == 0
    assert s._energy["p1"] == energy_before - s._move_cost


def test_move_blocked_by_player_costs_energy():
    s = _make_clear_scenario()
    _clear_area(s, 5, 5, 4)
    s._positions["p1"] = (5, 5)
    s._positions["p2"] = (6, 5)
    energy_before = s._energy["p1"]

    s.apply_turn({"p1": Action.MOVE_RIGHT, "p2": Action.WAIT})

    assert s._positions["p1"] == (5, 5)
    assert s._moves["p1"] == 0
    assert s._energy["p1"] == energy_before - s._move_cost
