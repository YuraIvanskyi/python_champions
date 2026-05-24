"""Phase 4: AI report generation with a mocked HTTP endpoint."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from engine.core.config import AiConfig, AnalysisConfig, AppConfig

_MOCK_RESPONSE = json.dumps({
    "choices": [
        {
            "message": {
                "content": (
                    "**Student summary:** Your bot gathered resources effectively.\n\n"
                    "**Teacher notes:**\n- Good loop structure.\n- Missing docstring.\n"
                    "- Avoid bare except."
                )
            }
        }
    ]
}).encode()


def _config_ai_enabled() -> AppConfig:
    cfg = AppConfig()
    cfg.analysis = AnalysisConfig(enable_ai=True)
    cfg.ai = AiConfig(
        base_url="http://localhost:8000/v1",
        health_check_url="http://localhost:8000/health",
    )
    return cfg


def _mock_urlopen(url, *args, **kwargs):
    resp = MagicMock()
    url_str = str(url.full_url if hasattr(url, "full_url") else url)
    if "health" in url_str:
        resp.status = 200
    else:
        resp.read.return_value = _MOCK_RESPONSE
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_ai_report_written(tmp_path: Path) -> None:
    """Mock HTTP → ai_report.md must be created with advisory header."""
    from ai import health as h
    h.reset_cache()

    metrics = {
        "scores": {"gameplay": 70, "code_quality": 80, "final": 73},
        "feedback": ["Avoid bare except clauses"],
        "gameplay": {"player_id": "student", "scenario_id": "resource_wars"},
        "static": {"ruff_violations": {"E501": 2}},
        "runtime": {"total_turns": 50},
    }
    (tmp_path / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")

    from engine.analysis.ai_report import generate_report

    with patch("urllib.request.urlopen", side_effect=_mock_urlopen):
        path = generate_report(tmp_path, _config_ai_enabled())

    assert path is not None
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "advisory" in text.lower() or "AI-generated" in text


def test_ai_report_has_advisory_header(tmp_path: Path) -> None:
    from ai import health as h
    h.reset_cache()

    metrics = {
        "scores": {"gameplay": 70, "code_quality": 80, "final": 73},
        "feedback": [],
        "gameplay": {"player_id": "student", "scenario_id": "resource_wars"},
        "static": {},
        "runtime": {"total_turns": 10},
    }
    (tmp_path / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")

    from engine.analysis.ai_report import generate_report

    with patch("urllib.request.urlopen", side_effect=_mock_urlopen):
        path = generate_report(tmp_path, _config_ai_enabled())

    assert path is not None
    text = path.read_text(encoding="utf-8")
    assert "⚠️" in text or "advisory" in text.lower()


def test_metrics_json_unchanged_after_report(tmp_path: Path) -> None:
    """Scores in metrics.json must not be modified by AI report generation."""
    from ai import health as h
    h.reset_cache()

    metrics = {
        "scores": {"gameplay": 70, "code_quality": 80, "final": 73},
        "feedback": [],
        "gameplay": {"player_id": "student", "scenario_id": "resource_wars"},
        "static": {},
        "runtime": {"total_turns": 10},
    }
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps(metrics), encoding="utf-8")

    from engine.analysis.ai_report import generate_report

    with patch("urllib.request.urlopen", side_effect=_mock_urlopen):
        generate_report(tmp_path, _config_ai_enabled())

    after = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert after["scores"] == metrics["scores"]


def test_report_not_written_when_vllm_offline(tmp_path: Path) -> None:
    """When health check fails, ai_report.md must not be written."""
    from ai import health as h
    h.reset_cache()

    metrics = {
        "scores": {"gameplay": 70, "code_quality": 80, "final": 73},
        "feedback": [],
        "gameplay": {"player_id": "student"},
        "static": {},
        "runtime": {"total_turns": 10},
    }
    (tmp_path / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")

    from engine.analysis.ai_report import generate_report

    with patch("urllib.request.urlopen", side_effect=ConnectionRefusedError()):
        path = generate_report(tmp_path, _config_ai_enabled())

    assert path is None
    assert not (tmp_path / "ai_report.md").exists()
