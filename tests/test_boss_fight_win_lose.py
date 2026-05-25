"""Win/lose conditions and scoring for boss fight."""

from __future__ import annotations

from engine.core.action import Action
from scenarios.boss_fight.game import BossFightScenario


def test_boss_defeated_triggers_finished() -> None:
    sc = BossFightScenario(seed=0, player_ids=["hero"])
    sc.setup()
    sc._boss_hp = 1  # one hit away
    sc._positions["hero"] = (sc._boss_x + 1, sc._boss_y)
    result = sc.apply_turn({"hero": Action.ATTACK})
    assert sc.is_finished()
    assert "boss_defeated" in result.events


def test_all_bots_dead_triggers_finished() -> None:
    sc = BossFightScenario(seed=0, player_ids=["hero"])
    sc.setup()
    sc._hp["hero"] = 1
    # Force boss to be adjacent and deal enough damage
    sc._boss_x = sc._positions["hero"][0] + 1
    sc._boss_y = sc._positions["hero"][1]
    sc._boss_damage = 4
    result = sc.apply_turn({"hero": Action.WAIT})
    assert sc.is_finished()
    assert "party_wiped" in result.events


def test_max_turns_triggers_finished() -> None:
    sc = BossFightScenario(seed=0, max_turns=3, player_ids=["hero"])
    sc.setup()
    for _ in range(3):
        sc.apply_turn({"hero": Action.WAIT})
    assert sc.is_finished()


def test_win_scores_sum_to_100() -> None:
    sc = BossFightScenario(seed=0, player_ids=["a", "b"])
    sc.setup()
    # a deals most damage, b deals some
    sc._damage_dealt["a"] = 6
    sc._damage_dealt["b"] = 4
    sc._boss_hp = 0  # boss defeated
    sc._finished = True
    scores = sc.calculate_score()
    assert scores["a"] + scores["b"] == 100


def test_win_score_proportional_to_damage() -> None:
    sc = BossFightScenario(seed=0, player_ids=["a", "b"])
    sc.setup()
    sc._damage_dealt["a"] = 10
    sc._damage_dealt["b"] = 0
    sc._boss_hp = 0
    sc._finished = True
    scores = sc.calculate_score()
    assert scores["a"] == 100
    assert scores["b"] == 0


def test_loss_scores_capped_below_100() -> None:
    sc = BossFightScenario(seed=0, player_ids=["hero"])
    sc.setup()
    sc._damage_dealt["hero"] = 5
    sc._boss_hp = 5  # boss alive (loss)
    scores = sc.calculate_score()
    assert scores["hero"] <= 79


def test_no_damage_gives_zero_score() -> None:
    sc = BossFightScenario(seed=0, player_ids=["hero"])
    sc.setup()
    # No damage dealt
    scores = sc.calculate_score()
    assert scores["hero"] == 0


def test_boss_metrics_recorded() -> None:
    sc = BossFightScenario(seed=0, player_ids=["hero"])
    sc.setup()
    sc._positions["hero"] = (sc._boss_x + 1, sc._boss_y)
    sc.apply_turn({"hero": Action.ATTACK})
    m = sc.boss_metrics()
    assert m["damage_dealt"]["hero"] == sc._attack_damage
    assert m["boss_hp_final"] == sc._boss_hp


def test_dead_bots_skipped_each_turn() -> None:
    sc = BossFightScenario(seed=0, player_ids=["dead", "alive"])
    sc.setup()
    sc._alive["dead"] = False
    sc._hp["dead"] = 0
    # Confirm dead bot actions are skipped (no error)
    result = sc.apply_turn({"dead": Action.ATTACK, "alive": Action.WAIT})
    # "alive" waited, "dead" was skipped
    assert any("alive_waited" in e for e in result.events)
