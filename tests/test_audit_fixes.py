"""Regression tests for game audit fixes."""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from engine.core.loader import BotLoadError, load_bot, student_player_id_for_path
from engine.core.replay import ReplaySession
from engine.core.session import write_session
from engine.core.turn_order import ordered_action_player_ids
from engine.core.turn_result import TurnResult
from engine.core.action import Action
from engine.paths import resource_root, writable_root
from engine.sandbox.constants import SANDBOX_WORKER_FLAG
from engine.sandbox.runner import _spawn_command
from engine.scoring.weights import load_scoring_weights


def test_student_player_id_zero_padded() -> None:
    assert student_player_id_for_path(Path("a.py"), 2, total=12) == "p02_a"
    assert student_player_id_for_path(Path("a.py"), 10, total=12) == "p10_a"


def test_turn_order_uses_setup_order() -> None:
    order = ["student", "opponent"]
    actions = {"opponent": Action.WAIT, "student": Action.GATHER}
    assert ordered_action_player_ids(order, actions) == ["student", "opponent"]


def test_loader_blocks_eval(tmp_path: Path) -> None:
    bot = tmp_path / "bad.py"
    bot.write_text("def make_turn(state):\n    eval('1')\n    return 'WAIT'\n")
    with pytest.raises(BotLoadError, match="eval"):
        load_bot(bot)


def test_scoring_weights_validation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    scenario_dir = tmp_path / "scenarios" / "resource_wars"
    scenario_dir.mkdir(parents=True)
    (scenario_dir / "scenario.toml").write_text(
        "[scoring]\ngameplay_weight = 0.9\ncode_weight = 0.5\n",
        encoding="utf-8",
    )

    def fake_read(scenario_id: str) -> dict:
        del scenario_id
        return {
            "scoring": {"gameplay_weight": 0.9, "code_weight": 0.5},
            "scenario": {},
        }

    monkeypatch.setattr("engine.scoring.weights.load_scenario_toml", fake_read)
    with pytest.raises(ValueError, match="sum to 1.0"):
        load_scoring_weights("resource_wars")


def test_replay_restores_boss_difficulty() -> None:
    replay = {
        "seed": 42,
        "scenario": "boss_fight",
        "boss_difficulty": 3,
        "player_ids": ["student"],
        "turns": [],
        "final_scores": {"student": 0},
    }
    session = ReplaySession(replay)
    assert getattr(session.scenario, "_difficulty", None) == 3


def test_write_session_snapshots_bot(tmp_path: Path) -> None:
    bot = tmp_path / "hero.py"
    bot.write_text("def make_turn(state):\n    return 'WAIT'\n")
    session_dir = write_session(
        tmp_path / "results",
        seed=1,
        scenario_id="resource_wars",
        bot_path=str(bot),
        player_ids=["student"],
        turn_log=[],
        final_scores={"student": 0},
        text_log=["ok"],
    )
    snap = session_dir / "bots" / "student.py"
    assert snap.is_file()
    replay = json.loads((session_dir / "replay.json").read_text(encoding="utf-8"))
    assert replay["bot_files"]["student"].endswith("bots/student.py")


def test_frozen_spawn_uses_worker_flag() -> None:
    with mock.patch("engine.sandbox.runner.is_frozen", return_value=True):
        cmd = _spawn_command(Path("bot.py"))
    assert cmd[1] == SANDBOX_WORKER_FLAG


def test_resource_root_uses_meipass_when_frozen(monkeypatch: pytest.MonkeyPatch) -> None:
    resource_root.cache_clear()
    writable_root.cache_clear()
    monkeypatch.setattr("engine.paths.is_frozen", lambda: True)
    monkeypatch.setattr("engine.paths.sys", mock.Mock(frozen=True, _MEIPASS="/bundle"))
    assert str(resource_root()).replace("\\", "/") == "/bundle"
    resource_root.cache_clear()
    writable_root.cache_clear()
