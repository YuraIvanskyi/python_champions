"""Test Energy Stations map setup: stations placed correctly, bots on valid cells."""

import pytest

from engine.simulation.map import TileType
from scenarios.energy_stations.game import EnergyStationsScenario


def _make_scenario(seed: int = 1, players: list[str] | None = None) -> EnergyStationsScenario:
    pids = players or ["p1", "p2"]
    s = EnergyStationsScenario(seed=seed, player_ids=pids)
    s.setup()
    return s


def test_stations_placed_with_correct_capacity():
    s = _make_scenario()
    assert s._map is not None
    # Count station tiles on map
    station_tiles = [
        (x, y)
        for x, y, t in s._map.iter_tiles()
        if t is TileType.STATION
    ]
    assert len(station_tiles) == len(s._station_capacities)
    for pos in station_tiles:
        assert pos in s._station_capacities
        assert s._station_capacities[pos] == s._initial_capacity


def test_station_count_matches_config():
    s = _make_scenario()
    assert len(s._station_capacities) == s._station_count


def test_bots_on_valid_empty_cells():
    s = _make_scenario(players=["a", "b", "c"])
    assert s._map is not None
    positions = list(s._positions.values())
    # All positions are within bounds
    for x, y in positions:
        assert s._map.in_bounds(x, y), f"Position {(x, y)} out of bounds"
        tile = s._map.get_tile(x, y)
        assert tile is TileType.EMPTY, f"Bot placed on {tile} at {(x, y)}"
    # No two bots on same cell
    assert len(set(positions)) == len(positions)


def test_bots_start_with_correct_energy():
    s = _make_scenario()
    for pid in s.player_ids():
        assert s._energy[pid] == s._starting_energy


def test_no_overlapping_obstacles_and_stations():
    s = _make_scenario(seed=42)
    assert s._map is not None
    for (sx, sy) in s._station_capacities:
        assert s._map.get_tile(sx, sy) is TileType.STATION


def test_player_limits():
    mn, mx = EnergyStationsScenario.player_limits()
    assert mn == 2
    assert mx == 8


def test_too_few_players_raises():
    with pytest.raises(ValueError):
        EnergyStationsScenario(seed=1, player_ids=["solo"])
