"""ATTACK reduces boss HP; HEAL_SELF/HEAL_ALLY restore HP correctly."""

from __future__ import annotations

from engine.core.action import Action
from scenarios.boss_fight.game import BossFightScenario


def _adjacent_scenario(seed: int = 0) -> tuple[BossFightScenario, str]:
    """Return a scenario with one bot placed adjacent to the boss."""
    sc = BossFightScenario(seed=seed, player_ids=["hero"])
    sc.setup()
    # Manually place the hero adjacent to the boss
    sc._positions["hero"] = (sc._boss_x + 1, sc._boss_y)
    return sc, "hero"


def test_attack_reduces_boss_hp() -> None:
    sc, pid = _adjacent_scenario()
    initial = sc._boss_hp
    sc.apply_turn({pid: Action.ATTACK})
    assert sc._boss_hp == initial - sc._attack_damage


def test_attack_when_not_adjacent_wasted() -> None:
    sc = BossFightScenario(seed=0, player_ids=["hero"])
    sc.setup()
    # Manually place hero far from boss
    sc._positions["hero"] = (0, 0)
    initial_boss_hp = sc._boss_hp
    result = sc.apply_turn({"hero": Action.ATTACK})
    assert sc._boss_hp == initial_boss_hp
    assert any("wasted" in e for e in result.events)


def test_heal_self_restores_hp() -> None:
    sc = BossFightScenario(seed=0, player_ids=["hero"])
    sc.setup()
    sc._hp["hero"] = 1
    sc.apply_turn({"hero": Action.HEAL_SELF})
    assert sc._hp["hero"] == min(sc._player_max_hp, 1 + sc._heal_amount)


def test_heal_self_capped_at_max() -> None:
    sc = BossFightScenario(seed=0, player_ids=["hero"])
    sc.setup()
    sc._hp["hero"] = sc._player_max_hp
    sc.apply_turn({"hero": Action.HEAL_SELF})
    assert sc._hp["hero"] == sc._player_max_hp


def test_heal_ally_targets_weakest() -> None:
    sc = BossFightScenario(seed=0, player_ids=["healer", "weak", "strong"])
    sc.setup()
    sc._hp["healer"] = sc._player_max_hp
    sc._hp["weak"] = 1
    sc._hp["strong"] = sc._player_max_hp
    before_weak = sc._hp["weak"]
    sc.apply_turn({
        "healer": Action.HEAL_ALLY,
        "weak": Action.WAIT,
        "strong": Action.WAIT,
    })
    assert sc._hp["weak"] == min(sc._player_max_hp, before_weak + sc._heal_amount)
    assert sc._hp["strong"] == sc._player_max_hp  # unchanged


def test_heal_ally_heals_self_when_no_allies() -> None:
    sc = BossFightScenario(seed=0, player_ids=["solo"])
    sc.setup()
    sc._hp["solo"] = 1
    sc.apply_turn({"solo": Action.HEAL_ALLY})
    assert sc._hp["solo"] == min(sc._player_max_hp, 1 + sc._heal_amount)


def test_damage_dealt_tracked() -> None:
    sc, pid = _adjacent_scenario()
    sc.apply_turn({pid: Action.ATTACK})
    assert sc._damage_dealt[pid] == sc._attack_damage


def test_heals_given_tracked() -> None:
    sc = BossFightScenario(seed=0, player_ids=["hero"])
    sc.setup()
    sc._hp["hero"] = 1
    sc.apply_turn({"hero": Action.HEAL_SELF})
    assert sc._heals_given["hero"] > 0
    assert sc._heals_received["hero"] > 0


def test_dead_bot_skipped() -> None:
    sc = BossFightScenario(seed=0, player_ids=["dead", "alive"])
    sc.setup()
    sc._alive["dead"] = False
    sc._hp["dead"] = 0
    sc._positions["alive"] = (sc._boss_x + 1, sc._boss_y)
    initial_boss_hp = sc._boss_hp
    sc.apply_turn({"dead": Action.ATTACK, "alive": Action.WAIT})
    # "dead" was skipped, boss HP unchanged from "alive" WAIT
    assert sc._boss_hp == initial_boss_hp
