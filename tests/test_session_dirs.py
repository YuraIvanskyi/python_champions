"""Session directory naming and listing."""

from __future__ import annotations

import json
from pathlib import Path

from engine.core.replay import (
    delete_all_sessions,
    delete_session_dir,
    list_session_dirs,
    session_list_label,
)
from engine.core.session import write_session


def test_write_session_uses_scenario_prefix(tmp_path: Path) -> None:
    session = write_session(
        tmp_path,
        seed=1,
        scenario_id="boss_fight",
        bot_path="student_bots/example.py",
        turn_log=[],
        final_scores={"student": 0},
        text_log=[],
    )
    assert session.name.startswith("boss_fight_session_")
    assert (session / "replay.json").is_file()


def test_list_session_dirs_legacy_and_prefixed(tmp_path: Path) -> None:
    legacy = tmp_path / "session_20200101T000000000000Z"
    legacy.mkdir()
    (legacy / "replay.json").write_text(
        json.dumps(
            {
                "seed": 1,
                "scenario": "resource_wars",
                "turns": [],
                "final_scores": {},
            }
        ),
        encoding="utf-8",
    )
    prefixed = tmp_path / "energy_stations_session_20200102T000000000000Z"
    prefixed.mkdir()
    (prefixed / "replay.json").write_text(
        json.dumps(
            {
                "seed": 2,
                "scenario": "energy_stations",
                "turns": [],
                "final_scores": {},
            }
        ),
        encoding="utf-8",
    )
    dirs = list_session_dirs(tmp_path)
    assert len(dirs) == 2
    assert set(dirs) == {legacy, prefixed}


def test_session_list_label_reads_scenario(tmp_path: Path) -> None:
    session = write_session(
        tmp_path,
        seed=3,
        scenario_id="resource_wars",
        bot_path="b.py",
        turn_log=[],
        final_scores={"student": 1},
        text_log=[],
    )
    label = session_list_label(session, "en")
    assert "resource" in label.lower() or "Resource" in label
    assert "·" in label


def test_delete_session_helpers(tmp_path: Path) -> None:
    s1 = write_session(
        tmp_path,
        seed=1,
        scenario_id="resource_wars",
        bot_path="b.py",
        turn_log=[],
        final_scores={},
        text_log=[],
    )
    s2 = write_session(
        tmp_path,
        seed=2,
        scenario_id="resource_wars",
        bot_path="b.py",
        turn_log=[],
        final_scores={},
        text_log=[],
    )
    delete_session_dir(s1)
    assert not s1.exists()
    assert s2.exists()
    assert delete_all_sessions(tmp_path) == 1
    assert list_session_dirs(tmp_path) == []
