"""Phase 4: Ollama health probe behaviour."""

from __future__ import annotations

import urllib.error
from unittest.mock import MagicMock, patch


def _make_resp(status: int = 200):
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_reachable_returns_true_on_200() -> None:
    from ai import health as h
    h.reset_cache()
    with patch("urllib.request.urlopen", return_value=_make_resp(200)):
        assert h.is_ollama_reachable("http://localhost:11434/api/tags", use_cache=False) is True


def test_reachable_returns_false_on_connection_refused() -> None:
    from ai import health as h
    h.reset_cache()
    with patch("urllib.request.urlopen", side_effect=ConnectionRefusedError()):
        assert h.is_ollama_reachable("http://localhost:11434/api/tags", use_cache=False) is False


def test_reachable_returns_false_on_timeout() -> None:
    from ai import health as h
    h.reset_cache()
    with patch("urllib.request.urlopen", side_effect=TimeoutError()):
        assert h.is_ollama_reachable("http://localhost:11434/api/tags", use_cache=False) is False


def test_reachable_returns_false_on_http_error() -> None:
    from ai import health as h
    h.reset_cache()
    exc = urllib.error.HTTPError(
        url="http://localhost:11434/api/tags",
        code=503,
        msg="Service Unavailable",
        hdrs=None,  # type: ignore[arg-type]
        fp=None,
    )
    with patch("urllib.request.urlopen", side_effect=exc):
        assert h.is_ollama_reachable("http://localhost:11434/api/tags", use_cache=False) is False


def test_reachable_caches_result() -> None:
    from ai import health as h
    h.reset_cache()
    with patch("urllib.request.urlopen", return_value=_make_resp(200)) as mock_open:
        h.is_ollama_reachable("http://localhost:11434/api/tags", use_cache=True)
        h.is_ollama_reachable("http://localhost:11434/api/tags", use_cache=True)
        assert mock_open.call_count == 1  # second call used cache


def test_reset_cache_forces_new_probe() -> None:
    from ai import health as h
    h.reset_cache()
    with patch("urllib.request.urlopen", return_value=_make_resp(200)) as mock_open:
        h.is_ollama_reachable("http://localhost:11434/api/tags", use_cache=True)
        h.reset_cache()
        h.is_ollama_reachable("http://localhost:11434/api/tags", use_cache=True)
        assert mock_open.call_count == 2


def test_get_loaded_model_returns_none_on_failure() -> None:
    from ai.health import get_loaded_model
    with patch("urllib.request.urlopen", side_effect=ConnectionRefusedError()):
        assert get_loaded_model("http://localhost:8000/v1") is None


def test_get_loaded_model_parses_response() -> None:
    import json
    from ai.health import get_loaded_model

    payload = json.dumps({"data": [{"id": "Qwen/Qwen2.5-1.5B-Instruct"}]}).encode()
    resp = MagicMock()
    resp.read.return_value = payload
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=resp):
        model = get_loaded_model("http://localhost:8000/v1")
    assert model == "Qwen/Qwen2.5-1.5B-Instruct"
