"""Replay and logs written after CLI run."""

import json
import subprocess
import sys
from pathlib import Path


def test_replay_written_after_run(tmp_path: Path) -> None:
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
    completed = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=Path.cwd())
    assert completed.returncode == 0

    sessions = list(results.glob("session_*"))
    assert len(sessions) == 1
    replay_path = sessions[0] / "replay.json"
    logs_path = sessions[0] / "logs.txt"
    assert replay_path.is_file()
    assert logs_path.is_file()

    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    assert replay["seed"] == 42
    assert replay["scenario"] == "resource_wars"
    assert len(replay["turns"]) > 0
    assert "final_scores" in replay
