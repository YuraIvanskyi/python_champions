"""Coach screen data: bot_files and metrics resolution."""

from __future__ import annotations

import json
from pathlib import Path

from ui.coach_data import (
    bot_path_for_player,
    coach_player_ids,
    load_metrics_block,
    player_ids_from_replay,
)


def test_bot_files_mapping(tmp_path: Path) -> None:
    replay = {
        "player_ids": ["alice", "bob"],
        "bots": ["student_bots/a.py", "student_bots/b.py"],
        "bot_files": {"alice": "student_bots/a.py", "bob": "student_bots/b.py"},
    }
    assert bot_path_for_player(replay, "bob") == Path("student_bots/b.py")


def test_metrics_block_per_player() -> None:
    metrics = {
        "players": {
            "p1": {"scores": {"final": 10}, "feedback_items": []},
            "p2": {"scores": {"final": 20}, "feedback_items": []},
        }
    }
    block = load_metrics_block(metrics, "p2")
    assert block["scores"]["final"] == 20


def test_metrics_block_single_player_practice() -> None:
    metrics = {
        "gameplay": {"player_id": "student", "raw_scores": {"student": 3, "opponent": 1}},
        "scores": {"final": 42.0, "gameplay": 60, "code_quality": 80},
    }
    assert load_metrics_block(metrics, "student")["scores"]["final"] == 42.0
    assert load_metrics_block(metrics, "opponent") == {}


def test_coach_player_ids_practice_excludes_opponent() -> None:
    metrics = {
        "gameplay": {"player_id": "student"},
        "scores": {"final": 1},
    }
    replay = {
        "player_ids": ["student", "opponent"],
        "players": {
            "student": {"display_name": "You", "is_student": True},
            "opponent": {"display_name": "Greedy", "is_student": False},
        },
        "bot_files": {"student": "student_bots/a.py"},
    }
    assert coach_player_ids(metrics, replay) == ["student"]


def test_replay_bot_files_written(tmp_path: Path) -> None:
    from engine.core.session import write_session

    session = write_session(
        tmp_path,
        seed=1,
        scenario_id="resource_wars",
        bot_path="student_bots/example_bot.py",
        bot_paths=["student_bots/example_bot.py"],
        player_ids=["student"],
        turn_log=[],
        final_scores={"student": 0},
        text_log=[],
    )
    replay = json.loads((session / "replay.json").read_text(encoding="utf-8"))
    assert replay.get("bot_files") == {"student": "student_bots/example_bot.py"}
    assert player_ids_from_replay(replay) == ["student"]
