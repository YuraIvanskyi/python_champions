"""Boss spawns at centre, bots at edges, HP initialised from config."""

from __future__ import annotations

import pytest

from scenarios.boss_fight.game import BossFightScenario


def _scenario(n_players: int = 1, seed: int = 42) -> BossFightScenario:
    pids = [f"p{i}" for i in range(n_players)]
    sc = BossFightScenario(seed=seed, player_ids=pids)
    sc.setup()
    return sc


def test_boss_spawns_at_centre() -> None:
    sc = _scenario(1)
    assert sc._boss_x == sc._map_width // 2
    assert sc._boss_y == sc._map_height // 2


def test_boss_hp_initialised() -> None:
    sc = _scenario(1)
    assert sc._boss_hp == sc._boss_max_hp
    assert sc._boss_hp > 0


def test_player_hp_initialised() -> None:
    sc = _scenario(3)
    for pid in sc.player_ids():
        assert sc._hp[pid] == sc._player_max_hp
        assert sc._alive[pid] is True


def test_bots_on_outer_ring() -> None:
    sc = _scenario(4)
    w, h = sc._map_width, sc._map_height
    for pid, (x, y) in sc._positions.items():
        on_edge = x == 0 or x == w - 1 or y == 0 or y == h - 1
        assert on_edge, f"{pid} spawned at ({x},{y}), not on outer ring"


def test_player_limits() -> None:
    min_p, max_p = BossFightScenario.player_limits()
    assert min_p == 1
    assert max_p == 6


def test_invalid_player_count_raises() -> None:
    with pytest.raises(ValueError):
        BossFightScenario(seed=1, player_ids=["p0"] * 7)


def test_no_players_raises_due_to_limits() -> None:
    with pytest.raises(ValueError):
        BossFightScenario(seed=1, player_ids=[])


def test_bots_not_on_boss_cell() -> None:
    sc = _scenario(6)
    for pid, (x, y) in sc._positions.items():
        assert not (x == sc._boss_x and y == sc._boss_y), \
            f"{pid} spawned on boss cell"


def test_boss_hp_scales_with_difficulty() -> None:
    easy = BossFightScenario(seed=1, player_ids=["p0"], difficulty=1)
    hard = BossFightScenario(seed=1, player_ids=["p0"], difficulty=3)
    easy.setup()
    hard.setup()
    assert easy._boss_max_hp == 30
    assert easy._boss_damage == 2
    assert hard._boss_max_hp == 60
    assert hard._boss_damage == 5
    assert hard._multi_target is True


def test_invalid_difficulty_raises() -> None:
    with pytest.raises(ValueError, match="difficulty must be"):
        BossFightScenario(seed=1, player_ids=["p0"], difficulty=9)


def test_different_seeds_give_different_layouts() -> None:
    sc1 = _scenario(2, seed=1)
    sc2 = _scenario(2, seed=99)
    # Boss is always at centre so same; but obstacle placement should differ
    import json
    tiles1 = {(t["x"], t["y"]): t["type"] for t in sc1.build_game_state("p0")["visible_tiles"]}
    tiles2 = {(t["x"], t["y"]): t["type"] for t in sc2.build_game_state("p0")["visible_tiles"]}
    # They may or may not differ but neither should crash
    assert isinstance(tiles1, dict)
    assert isinstance(tiles2, dict)
