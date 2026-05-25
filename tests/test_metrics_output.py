"""CLI run writes metrics.json with required structure."""

import json
import subprocess
import sys
from pathlib import Path


def test_run_writes_metrics_json(tmp_path: Path) -> None:
    results = tmp_path / "results"
    cmd = [
        sys.executable,
        "-m",
        "engine.cli",
        "run",
        "--scenario",
        "resource_wars",
        "--bot",
        "student_bots/resource_wars/example_bot.py",
        "--seed",
        "1",
        "--results-dir",
        str(results),
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=Path.cwd())
    assert completed.returncode == 0
    assert "Final score:" in completed.stdout

    sessions = list(results.glob("session_*"))
    assert len(sessions) == 1
    metrics_path = sessions[0] / "metrics.json"
    assert metrics_path.is_file()

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert "gameplay" in metrics
    assert "static" in metrics
    assert "runtime" in metrics
    assert "scores" in metrics
    assert "feedback" in metrics
    assert "gameplay" in metrics["scores"]
    assert "code_quality" in metrics["scores"]
    assert "final" in metrics["scores"]
    assert isinstance(metrics["feedback"], list)
    assert len(metrics["feedback"]) >= 1


def test_no_analysis_skips_metrics(tmp_path: Path) -> None:
    results = tmp_path / "results"
    cmd = [
        sys.executable,
        "-m",
        "engine.cli",
        "run",
        "--scenario",
        "resource_wars",
        "--bot",
        "student_bots/resource_wars/example_bot.py",
        "--seed",
        "1",
        "--results-dir",
        str(results),
        "--no-analysis",
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=Path.cwd())
    sessions = list(results.glob("session_*"))
    assert len(sessions) == 1
    assert not (sessions[0] / "metrics.json").exists()
