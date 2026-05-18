"""Replay JSON loads and steps through ReplaySession."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from engine.core.action import Action
from engine.core.replay import ReplaySession, load_replay


def _write_minimal_replay(path: Path) -> None:
    payload = {
        "seed": 7,
        "scenario": "resource_wars",
        "bot": "student_bots/example_bot.py",
        "turns": [
            {
                "turn": 1,
                "actions": {"student": "WAIT", "opponent": "WAIT"},
                "scores": {"student": 0, "opponent": 0},
                "events": [],
            }
        ],
        "final_scores": {"student": 0, "opponent": 0},
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_load_replay_from_fixture(tmp_path: Path) -> None:
    replay_path = tmp_path / "replay.json"
    _write_minimal_replay(replay_path)
    data = load_replay(replay_path)
    assert data["seed"] == 7
    assert data["scenario"] == "resource_wars"


def test_replay_session_steps(tmp_path: Path) -> None:
    replay_path = tmp_path / "replay.json"
    _write_minimal_replay(replay_path)
    session = ReplaySession.from_path(replay_path)

    initial = session.get_render_state()
    assert initial["turn"] == 0

    result = session.step_forward()
    assert result is not None
    assert result.turn_number == 1
    assert result.actions["student"] is Action.WAIT

    after = session.get_render_state()
    assert after["turn"] == 1


def test_replay_players_metadata(tmp_path: Path) -> None:
    replay_path = tmp_path / "replay.json"
    payload = {
        "seed": 1,
        "scenario": "resource_wars",
        "bot": "student_bots/example_bot.py",
        "opponent_mode": "dumb",
        "players": {
            "student": {"id": "student", "display_name": "Explorer", "icon": None},
            "opponent": {"id": "opponent", "display_name": "Rookie", "icon": None},
        },
        "turns": [],
        "final_scores": {"student": 0, "opponent": 0},
    }
    replay_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    session = ReplaySession.from_path(replay_path)
    assert session.players["student"].display_name == "Explorer"
    assert session.players["opponent"].display_name == "Rookie"
    state = session.get_render_state()
    assert state["display_names"]["student"] == "Explorer"


def test_replay_session_from_cli_run(tmp_path: Path) -> None:
    results = tmp_path / "results"
    cmd = [
        sys.executable,
        "-m",
        "engine.cli",
        "run",
        "--scenario",
        "resource_wars",
        "--bot",
        "student_bots/example_bot.py",
        "--seed",
        "42",
        "--results-dir",
        str(results),
    ]
    subprocess.run(cmd, check=True, capture_output=True, cwd=Path.cwd())
    replay_path = next(results.glob("session_*/replay.json"))
    session = ReplaySession.from_path(replay_path)
    assert session.turn_count > 0
    session.seek(session.turn_count - 1)
    assert session.get_render_state()["scores"] == session.final_scores
