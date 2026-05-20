"""Dumb opponent AI smoke tests."""

from __future__ import annotations

import random
from pathlib import Path

from engine.core.action import Action
from engine.core.config import load_config
from engine.core.game import run_game
from engine.core.loader import load_bot
from engine.simulation.dumb_ai import dumb_turn
from engine.simulation.simple_ai import greedy_turn

_LEGAL = {
    Action.MOVE_UP,
    Action.MOVE_DOWN,
    Action.MOVE_LEFT,
    Action.MOVE_RIGHT,
    Action.GATHER,
    Action.WAIT,
}


def _sample_state() -> dict:
    return {
        "position": [2, 2],
        "resources": 0,
        "on_resource": False,
        "map_width": 8,
        "map_height": 8,
        "visible_tiles": [
            {"x": x, "y": y, "type": "empty"}
            for x in range(8)
            for y in range(8)
        ],
    }


def test_dumb_turn_returns_legal_action() -> None:
    rng = random.Random(0)
    for _ in range(50):
        action = dumb_turn(_sample_state(), rng)
        assert action in _LEGAL


def test_dumb_opponent_scores_lower_than_greedy() -> None:
    bot = load_bot(Path("student_bots/example_bot.py"))
    config = load_config()
    seed = 42
    max_turns = 40

    dumb_result = run_game(
        scenario_id="resource_wars",
        student_bots=[bot],
        seed=seed,
        config=config,
        opponent_mode="dumb",
        max_turns=max_turns,
        write_results=False,
        print_summary=False,
    )
    greedy_result = run_game(
        scenario_id="resource_wars",
        student_bots=[bot],
        seed=seed,
        config=config,
        opponent_mode="greedy",
        max_turns=max_turns,
        write_results=False,
        print_summary=False,
    )

    assert dumb_result.final_scores["opponent"] <= greedy_result.final_scores["opponent"]
    assert dumb_result.final_scores["student"] >= greedy_result.final_scores["student"]


def test_greedy_still_gathers_on_resource() -> None:
    state = _sample_state()
    state["on_resource"] = True
    assert greedy_turn(state, random.Random(1)) is Action.GATHER
