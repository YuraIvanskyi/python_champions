"""Boss Fight practice mode adds a built-in ally alongside the student bot."""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.core.config import load_config
from engine.core.live_game import LiveGame
from engine.core.loader import load_bot


@pytest.fixture
def starter_bot():
    path = Path("student_bots/boss_fight/boss_fight_starter.py")
    if not path.is_file():
        pytest.skip("boss fight starter bot missing")
    return load_bot(path)


def test_boss_fight_practice_adds_computer_ally(starter_bot) -> None:
    config = load_config()
    live = LiveGame(
        scenario_id="boss_fight",
        student_bots=[starter_bot],
        seed=42,
        config=config,
        opponent_mode="dumb",
    )

    assert live.opponent_mode == "dumb"
    assert live.opponent_player is not None
    assert live.players.keys() == {"student", "opponent"}
    assert live.scenario.player_ids() == ["student", "opponent"]

    state = live.get_render_state()
    entity_ids = {e["id"] for e in state["entities"]}
    assert entity_ids == {"student", "opponent"}
    assert state.get("boss_entity") is not None


def test_boss_fight_classroom_skips_computer_ally(starter_bot) -> None:
    config = load_config()
    bot2 = load_bot(
        Path("student_bots/boss_fight/anna_bot.py"),
        player_id="anna",
    )
    if not Path("student_bots/boss_fight/anna_bot.py").is_file():
        pytest.skip("second boss fight bot missing")

    live = LiveGame(
        scenario_id="boss_fight",
        student_bots=[starter_bot, bot2],
        seed=42,
        config=config,
        opponent_mode=None,
    )

    assert live.opponent_player is None
    assert set(live.scenario.player_ids()) == {"student", "anna"}
