"""Phase 4: Timeout and error resilience."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from engine.core.config import AiConfig, AnalysisConfig, AppConfig


def _config_ai_enabled() -> AppConfig:
    cfg = AppConfig()
    cfg.analysis = AnalysisConfig(enable_ai=True)
    cfg.ai = AiConfig(
        base_url="http://localhost:8000/v1",
        health_check_url="http://localhost:8000/health",
        timeout_seconds=5.0,
    )
    return cfg


def _health_ok_then_timeout(url, *args, **kwargs):
    """First call (health check) succeeds; subsequent calls time out."""
    url_str = str(url.full_url if hasattr(url, "full_url") else url)
    if "health" in url_str:
        resp = MagicMock()
        resp.status = 200
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp
    raise TimeoutError("simulated timeout")


def test_complete_returns_none_on_timeout() -> None:
    """client.complete() must return None (not raise) on TimeoutError."""
    from ai import health as h
    h.reset_cache()

    from ai.client import complete

    with patch("urllib.request.urlopen", side_effect=_health_ok_then_timeout):
        result = complete("system", "user", _config_ai_enabled())

    assert result is None


def test_generate_report_returns_none_on_timeout(tmp_path: Path) -> None:
    """generate_report() must return None gracefully when the LLM times out."""
    from ai import health as h
    h.reset_cache()

    metrics = {
        "scores": {"gameplay": 70, "code_quality": 80, "final": 73},
        "feedback": ["Something"],
        "gameplay": {"player_id": "student", "scenario_id": "resource_wars"},
        "static": {},
        "runtime": {"total_turns": 50},
    }
    (tmp_path / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")

    from engine.analysis.ai_report import generate_report

    with patch("urllib.request.urlopen", side_effect=_health_ok_then_timeout):
        path = generate_report(tmp_path, _config_ai_enabled())

    # Timeout path: report is still written but with "unavailable" message
    # OR path is None — both are acceptable non-crashing outcomes.
    if path is not None:
        assert path.is_file()
        text = path.read_text(encoding="utf-8")
        assert "unavailable" in text.lower() or "timed out" in text.lower() or "advisory" in text.lower()


def test_complete_returns_none_on_http_error() -> None:
    """client.complete() must return None on HTTP 500 error."""
    import urllib.error
    from ai import health as h
    h.reset_cache()

    from ai.client import complete

    def _side_effect(url, *args, **kwargs):
        url_str = str(url.full_url if hasattr(url, "full_url") else url)
        if "health" in url_str:
            resp = MagicMock()
            resp.status = 200
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp
        raise urllib.error.HTTPError(
            url="http://localhost:8000/v1/chat/completions",
            code=500,
            msg="Internal Server Error",
            hdrs=None,  # type: ignore[arg-type]
            fp=None,
        )

    with patch("urllib.request.urlopen", side_effect=_side_effect):
        result = complete("system", "user", _config_ai_enabled())

    assert result is None


def test_generate_report_never_raises(tmp_path: Path) -> None:
    """generate_report() must not propagate any exception to the caller."""
    from ai import health as h
    h.reset_cache()

    (tmp_path / "metrics.json").write_text("{}", encoding="utf-8")

    from engine.analysis.ai_report import generate_report

    with patch("urllib.request.urlopen", side_effect=RuntimeError("unexpected")):
        try:
            result = generate_report(tmp_path, _config_ai_enabled())
        except Exception as exc:  # noqa: BLE001
            pytest.fail(f"generate_report raised unexpectedly: {exc}")
