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

    from engine.core.replay import list_session_dirs

    sessions = list_session_dirs(results)
    assert len(sessions) == 2
    replay_a = json.loads((sessions[0] / "replay.json").read_text(encoding="utf-8"))
    replay_b = json.loads((sessions[1] / "replay.json").read_text(encoding="utf-8"))

    def _game_payload(replay: dict) -> dict:
        return {
            "seed": replay["seed"],
            "scenario": replay["scenario"],
            "turns": replay["turns"],
            "final_scores": replay["final_scores"],
            "player_ids": replay.get("player_ids"),
            "opponent_mode": replay.get("opponent_mode"),
            "boss_difficulty": replay.get("boss_difficulty"),
        }

    assert _game_payload(replay_a) == _game_payload(replay_b)
