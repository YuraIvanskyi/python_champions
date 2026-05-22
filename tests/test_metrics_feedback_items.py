"""CLI run writes feedback_items in metrics.json."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_run_writes_feedback_items(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    bot = repo / "student_bots" / "example_bot.py"
    results = tmp_path / "results"
    results.mkdir()
    cmd = [
        sys.executable,
        "-m",
        "engine.cli",
        "run",
        "--scenario",
        "resource_wars",
        "--bot",
        str(bot),
        "--seed",
        "7",
        "--results-dir",
        str(results),
    ]
    subprocess.run(cmd, cwd=repo, check=True, capture_output=True, text=True)
    sessions = sorted(results.glob("session_*"))
    assert sessions
    metrics = json.loads((sessions[0] / "metrics.json").read_text(encoding="utf-8"))
    assert "feedback_items" in metrics
    assert isinstance(metrics["feedback_items"], list)
    assert len(metrics["feedback_items"]) >= 1
    item = metrics["feedback_items"][0]
    assert "id" in item and "title" in item and "panel" in item
    assert "feedback" in metrics
    assert isinstance(metrics["feedback"], list)
