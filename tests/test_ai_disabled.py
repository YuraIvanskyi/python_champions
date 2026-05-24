"""Phase 4: AI report is fully skipped when enable_ai = false."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from engine.core.config import AppConfig, AnalysisConfig


def _config(enable_ai: bool = False) -> AppConfig:
    cfg = AppConfig()
    cfg.analysis = AnalysisConfig(enable_ai=enable_ai)
    return cfg


def test_complete_returns_none_when_disabled() -> None:
    """ai.client.complete() must return None immediately when enable_ai = false."""
    from ai.client import complete

    result = complete("sys", "user", _config(enable_ai=False))
    assert result is None


def test_complete_makes_no_network_call_when_disabled() -> None:
    """No urllib call should be made when enable_ai = false."""
    from ai.client import complete

    with patch("urllib.request.urlopen") as mock_open:
        complete("sys", "user", _config(enable_ai=False))
        mock_open.assert_not_called()


def test_generate_report_returns_none_when_disabled(tmp_path: Path) -> None:
    """generate_report() must return None and not write ai_report.md when disabled."""
    from engine.analysis.ai_report import generate_report

    # Write a minimal metrics.json so the file-not-found path isn't triggered
    metrics = {
        "scores": {"gameplay": 70, "code_quality": 80, "final": 73},
        "feedback": [],
        "gameplay": {"player_id": "student"},
        "static": {},
        "runtime": {"total_turns": 10},
    }
    (tmp_path / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")

    result = generate_report(tmp_path, _config(enable_ai=False))

    assert result is None
    assert not (tmp_path / "ai_report.md").exists()


def test_generate_report_no_network_when_disabled(tmp_path: Path) -> None:
    """generate_report() must make zero network calls when enable_ai = false."""
    from engine.analysis.ai_report import generate_report

    (tmp_path / "metrics.json").write_text("{}", encoding="utf-8")

    with patch("urllib.request.urlopen") as mock_open:
        generate_report(tmp_path, _config(enable_ai=False))
        mock_open.assert_not_called()
