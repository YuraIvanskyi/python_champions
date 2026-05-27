"""Boss AI: level 1 moves toward nearest bot; level 2/3 target logic."""

from __future__ import annotations

from engine.core.action import Action
from scenarios.boss_fight.game import BossFightScenario


def _make_scenario(difficulty: int, player_ids: list[str], seed: int = 0) -> BossFightScenario:
    sc = BossFightScenario(seed=seed, player_ids=player_ids, difficulty=difficulty)
    sc.setup()
    return sc


def test_level1_boss_moves_toward_nearest_bot() -> None:
    sc = _make_scenario(1, ["p0"])
    # Place bot at top-left, boss is at centre
    sc._positions["p0"] = (0, 0)
    boss_before = (sc._boss_x, sc._boss_y)
    sc.apply_turn({"p0": Action.WAIT})
    boss_after = (sc._boss_x, sc._boss_y)
    # Boss should have moved closer to (0, 0)
    before_dist = abs(boss_before[0] - 0) + abs(boss_before[1] - 0)
    after_dist = abs(boss_after[0] - 0) + abs(boss_after[1] - 0)
    assert after_dist < before_dist


def test_level2_boss_attacks_lowest_hp_adjacent() -> None:
    sc = _make_scenario(2, ["low_hp", "high_hp"])
    # Place both adjacent to boss
    sc._positions["low_hp"] = (sc._boss_x + 1, sc._boss_y)
    sc._positions["high_hp"] = (sc._boss_x - 1, sc._boss_y)
    sc._hp["low_hp"] = 1
    sc._hp["high_hp"] = sc._player_max_hp
    hp_low_before = sc._hp["low_hp"]
    hp_high_before = sc._hp["high_hp"]
    sc.apply_turn({"low_hp": Action.WAIT, "high_hp": Action.WAIT})
    # Level 2 should target lowest HP bot
    assert sc._hp["low_hp"] < hp_low_before or sc._hp["high_hp"] < hp_high_before


def test_level3_boss_attacks_up_to_2_adjacent() -> None:
    sc = _make_scenario(3, ["p0", "p1", "p2"])
    # Place all three adjacent to boss
    sc._positions["p0"] = (sc._boss_x + 1, sc._boss_y)
    sc._positions["p1"] = (sc._boss_x - 1, sc._boss_y)
    sc._positions["p2"] = (sc._boss_x, sc._boss_y + 1)
    sc._hp["p0"] = sc._player_max_hp
    sc._hp["p1"] = sc._player_max_hp
    sc._hp["p2"] = sc._player_max_hp
    result = sc.apply_turn({"p0": Action.WAIT, "p1": Action.WAIT, "p2": Action.WAIT})
    attacked = sum(
        1 for e in result.events if e.startswith("boss_attacked_")
    )
    assert attacked <= 2, f"Level 3 boss attacked {attacked} > 2 targets"
    assert attacked >= 1, "Level 3 boss should attack at least 1 adjacent bot"


def test_level3_boss_attacks_lowest_hp_first() -> None:
    sc = _make_scenario(3, ["fragile", "tough"])
    sc._positions["fragile"] = (sc._boss_x + 1, sc._boss_y)
    sc._positions["tough"] = (sc._boss_x - 1, sc._boss_y)
    sc._hp["fragile"] = 1
    sc._hp["tough"] = sc._player_max_hp
    result = sc.apply_turn({"fragile": Action.WAIT, "tough": Action.WAIT})
    assert "boss_attacked_fragile" in result.events


def test_boss_blocked_by_obstacles() -> None:
    sc = BossFightScenario(seed=99, player_ids=["p0"])
    sc.setup()
    # Surround boss with obstacles on all 4 sides
    from engine.simulation.map import TileType
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        nx, ny = sc._boss_x + dx, sc._boss_y + dy
        if sc._map.in_bounds(nx, ny):  # type: ignore[arg-type]
            sc._map.set_tile(nx, ny, TileType.OBSTACLE)  # type: ignore[union-attr]
    boss_before = (sc._boss_x, sc._boss_y)
    sc._positions["p0"] = (0, 0)
    sc.apply_turn({"p0": Action.WAIT})
    # Boss should not have moved
    assert (sc._boss_x, sc._boss_y) == boss_before
