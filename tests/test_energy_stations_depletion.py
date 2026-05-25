"""Test station depletion: station at 0 capacity becomes EMPTY; is_finished on full depletion."""

from engine.core.action import Action
from engine.simulation.map import TileType
from scenarios.energy_stations.game import EnergyStationsScenario


def _make_scenario_one_station() -> tuple[EnergyStationsScenario, tuple[int, int]]:
    """Create a scenario with a single station of low capacity next to p1."""
    s = EnergyStationsScenario(seed=3, player_ids=["p1", "p2"])
    s.setup()
    assert s._map is not None

    # Clear all existing stations and place one manually
    for (sx, sy) in list(s._station_capacities.keys()):
        s._map.set_tile(sx, sy, TileType.EMPTY)
    s._station_capacities.clear()

    # Find a clear cell to place a station and bot adjacent to it
    for y in range(2, s._map.height - 2):
        for x in range(2, s._map.width - 2):
            if (
                s._map.get_tile(x, y) is TileType.EMPTY
                and s._map.get_tile(x + 1, y) is TileType.EMPTY
            ):
                s._map.set_tile(x, y, TileType.STATION)
                s._station_capacities[(x, y)] = s._gather_rate  # capacity for exactly 1 gather
                s._positions["p1"] = (x + 1, y)
                s._positions["p2"] = (0, 0)  # far away
                return s, (x, y)

    raise RuntimeError("Could not place test station")


def test_station_becomes_empty_on_depletion():
    s, (sx, sy) = _make_scenario_one_station()
    assert s._map is not None
    assert s._map.get_tile(sx, sy) is TileType.STATION

    actions = {"p1": Action.GATHER, "p2": Action.WAIT}
    s.apply_turn(actions)

    # Station tile is now EMPTY
    assert s._map.get_tile(sx, sy) is TileType.EMPTY
    assert (sx, sy) not in s._station_capacities


def test_is_finished_when_all_stations_depleted():
    s, (sx, sy) = _make_scenario_one_station()
    assert not s.is_finished()

    actions = {"p1": Action.GATHER, "p2": Action.WAIT}
    s.apply_turn(actions)

    # All stations depleted → game ends
    assert s.is_finished()


def test_partial_depletion_does_not_finish_game():
    """Deplete exactly one of multiple stations; game should still be running."""
    s = EnergyStationsScenario(seed=5, player_ids=["p1", "p2"])
    s.setup()
    assert s._map is not None
    initial_count = len(s._station_capacities)
    assert initial_count > 1

    # Pick any station and reduce its capacity to exactly gather_rate.
    # Use _make_scenario_one_station logic: find a station whose adjacent cell
    # is EMPTY and NOT adjacent to any other station (prevents gather redirecting).
    target_station = None
    bot_pos = None
    from scenarios.energy_stations.game import ORTHOGONAL_DELTAS
    for (sx, sy) in list(s._station_capacities.keys()):
        for dx, dy in ORTHOGONAL_DELTAS:
            cx, cy = sx + dx, sy + dy
            if not (s._map.in_bounds(cx, cy) and s._map.get_tile(cx, cy) is TileType.EMPTY):
                continue
            # Ensure (cx, cy) is not adjacent to any OTHER station
            other_adj = [
                (nx, ny) for ndx, ndy in ORTHOGONAL_DELTAS
                for nx, ny in [(cx + ndx, cy + ndy)]
                if s._map.in_bounds(nx, ny)
                and s._map.get_tile(nx, ny) is TileType.STATION
                and (nx, ny) != (sx, sy)
            ]
            if not other_adj:
                target_station = (sx, sy)
                bot_pos = (cx, cy)
                break
        if target_station:
            break

    if target_station is None:
        pytest.skip("Could not find isolated station in this seed")

    sx, sy = target_station
    # Set only this station to capacity = gather_rate so one gather depletes it
    s._station_capacities[(sx, sy)] = s._gather_rate
    s._positions["p1"] = bot_pos
    # Put p2 far from any station
    for y in range(s._map.height):
        for x in range(s._map.width):
            if (
                s._map.get_tile(x, y) is TileType.EMPTY
                and (x, y) != bot_pos
                and not any(
                    s._map.in_bounds(x + ndx, y + ndy)
                    and s._map.get_tile(x + ndx, y + ndy) is TileType.STATION
                    for ndx, ndy in ORTHOGONAL_DELTAS
                )
            ):
                s._positions["p2"] = (x, y)
                break
        else:
            continue
        break

    actions = {"p1": Action.GATHER, "p2": Action.WAIT}
    s.apply_turn(actions)

    # One station depleted but others remain → game still active
    assert not s.is_finished()
    assert (sx, sy) not in s._station_capacities


def test_is_finished_on_max_turns():
    s = EnergyStationsScenario(seed=1, player_ids=["p1", "p2"], max_turns=3)
    s.setup()
    for _ in range(3):
        assert not s.is_finished() or _ == 2
        s.apply_turn({"p1": Action.WAIT, "p2": Action.WAIT})
    assert s.is_finished()
