"""Same seed produces identical replay content."""

import json
import subprocess
import sys
from pathlib import Path


def test_identical_replay_for_same_seed(tmp_path: Path) -> None:
    results = tmp_path / "results"
    cmd_base = [
        sys.executable,
        "-m",
        "engine.cli",
        "run",
        "--scenario",
        "resource_wars",
        "--bot",
        "student_bots/resource_wars/example_bot.py",
        "--seed",
        "42",
        "--results-dir",
        str(results),
    ]
    subprocess.run(cmd_base, check=True, capture_output=True, cwd=Path.cwd())
    subprocess.run(cmd_base, check=True, capture_output=True, cwd=Path.cwd())

    sessions = sorted(results.glob("session_*"))
    assert len(sessions) == 2
    replay_a = json.loads((sessions[0] / "replay.json").read_text(encoding="utf-8"))
    replay_b = json.loads((sessions[1] / "replay.json").read_text(encoding="utf-8"))
    assert replay_a == replay_b
