"""Unit tests for turn-event action effect spawning."""

from __future__ import annotations

from engine.core.action import Action
from engine.core.turn_result import TurnResult
from ui.render.action_effects import spawn_effects_from_turn


def _render_state(**overrides):
    base = {
        "entities": [
            {"id": "student", "position": [2, 3]},
            {"id": "opponent", "position": [4, 3]},
        ],
        "boss_entity": {"position": [5, 5]},
    }
    base.update(overrides)
    return base


def test_spawn_gather_resource_effect() -> None:
    turn = TurnResult(
        turn_number=1,
        actions={"student": Action.GATHER},
        scores={"student": 1},
        events=["student_gathered"],
    )
    effects = spawn_effects_from_turn(turn, _render_state(), scenario_id="resource_wars")
    assert len(effects) == 1
    assert effects[0].kind == "gather_resource"
    assert (effects[0].tile_x, effects[0].tile_y) == (2, 3)


def test_spawn_gather_mana_effect() -> None:
    turn = TurnResult(
        turn_number=1,
        actions={"student": Action.GATHER},
        scores={"student": 0},
        events=["student_gathered_5"],
    )
    render_state = _render_state(station_capacities={"3,4": 20})
    effects = spawn_effects_from_turn(turn, render_state, scenario_id="energy_stations")
    assert len(effects) == 1
    assert effects[0].kind == "gather_mana"


def test_spawn_attack_and_hit_on_boss() -> None:
    turn = TurnResult(
        turn_number=1,
        actions={"student": Action.ATTACK},
        scores={"student": 0},
        events=["student_attacked_boss"],
    )
    effects = spawn_effects_from_turn(turn, _render_state(), scenario_id="boss_fight")
    kinds = {e.kind for e in effects}
    assert kinds == {"attack", "hit"}


def test_spawn_boss_attack_hit() -> None:
    turn = TurnResult(
        turn_number=1,
        actions={"student": Action.WAIT},
        scores={"student": 0},
        events=["boss_attacked_student"],
    )
    effects = spawn_effects_from_turn(turn, _render_state(), scenario_id="boss_fight")
    assert any(e.kind == "hit" and e.tile_x == 2 and e.tile_y == 3 for e in effects)
    assert any(e.kind == "attack" and e.tile_x == 5 and e.tile_y == 5 for e in effects)


def test_spawn_heal_and_push_effects() -> None:
    self_heal = TurnResult(
        turn_number=1,
        actions={"student": Action.HEAL_SELF},
        scores={"student": 0},
        events=["student_healed_self_8"],
    )
    assert spawn_effects_from_turn(self_heal, _render_state(), scenario_id="boss_fight")[0].kind == "heal"

    ally_heal = TurnResult(
        turn_number=1,
        actions={"student": Action.HEAL_ALLY},
        scores={"student": 0},
        events=["student_healed_ally_opponent_6"],
    )
    ally_effects = spawn_effects_from_turn(ally_heal, _render_state(), scenario_id="boss_fight")
    assert {e.kind for e in ally_effects} == {"heal", "healed"}

    push = TurnResult(
        turn_number=1,
        actions={"student": Action.ATTACK},
        scores={"student": 0},
        events=["student_pushed_opponent"],
    )
    push_effects = spawn_effects_from_turn(push, _render_state(), scenario_id="energy_stations")
    assert {e.kind for e in push_effects} == {"attack", "hit"}
