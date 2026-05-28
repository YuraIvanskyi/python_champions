"""Synchronous connectivity probe for Ollama / OpenAI-compatible servers."""

from __future__ import annotations

import logging
import urllib.error
import urllib.request

log = logging.getLogger(__name__)

# Per-session cache: None = not checked yet, bool = last result
_cached_reachable: bool | None = None


def is_ollama_reachable(
    health_check_url: str,
    *,
    timeout: float = 3.0,
    use_cache: bool = True,
) -> bool:
    """Return True if the Ollama health endpoint responds with HTTP 200.

    Results are cached for the session lifetime. Pass ``use_cache=False``
    (e.g. from the Retry button) to force a fresh probe.
    """
    global _cached_reachable  # noqa: PLW0603
    if use_cache and _cached_reachable is not None:
        return _cached_reachable

    result = _probe(health_check_url, timeout)
    _cached_reachable = result
    return result


def reset_cache() -> None:
    """Invalidate the cached health result (e.g. after user presses Retry)."""
    global _cached_reachable  # noqa: PLW0603
    _cached_reachable = None


def get_loaded_model(base_url: str, *, timeout: float = 3.0) -> str | None:
    """Return the first model id reported by GET {base_url}/models, or None."""
    try:
        url = base_url.rstrip("/") + "/models"
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
            import json

            data = json.loads(resp.read().decode())
            models = data.get("data", [])
            if models:
                return str(models[0].get("id", ""))
    except Exception as exc:  # noqa: BLE001
        log.debug("get_loaded_model failed: %s", exc)
    return None


# ── internal ──────────────────────────────────────────────────────────────────


def _probe(url: str, timeout: float) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
            return resp.status == 200
    except urllib.error.HTTPError as exc:
        log.debug("Ollama health check HTTP error %s: %s", exc.code, url)
        return False
    except Exception as exc:  # noqa: BLE001
        log.debug("Ollama health check failed: %s", exc)
        return False
