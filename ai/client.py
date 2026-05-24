"""Thin OpenAI-compatible HTTP client for vLLM with graceful fallback."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import TYPE_CHECKING

from ai.health import is_vllm_reachable

if TYPE_CHECKING:
    from engine.core.config import AppConfig

log = logging.getLogger(__name__)

# Set OPENAI_API_KEY in environment if targeting a cloud-compatible endpoint.
# By default vLLM does not require a key, so this is unused.


def complete(system: str, user: str, config: "AppConfig") -> str | None:
    """Generate a chat completion; return assistant text or None on any failure.

    Returns None immediately (zero network calls) when ``enable_ai`` is False.
    """
    if not config.analysis.enable_ai:
        return None

    ai_cfg = config.ai
    if not is_vllm_reachable(ai_cfg.health_check_url):
        log.warning("vLLM not reachable — skipping AI completion")
        return None

    payload = {
        "model": ai_cfg.model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": ai_cfg.max_tokens,
    }
    endpoint = ai_cfg.base_url.rstrip("/") + "/chat/completions"

    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=ai_cfg.timeout_seconds) as resp:  # noqa: S310
            body = json.loads(resp.read().decode())
            choices = body.get("choices", [])
            if not choices:
                log.warning("vLLM returned empty choices")
                return None
            return str(choices[0]["message"]["content"])
    except TimeoutError:
        log.warning("vLLM request timed out after %.0fs", ai_cfg.timeout_seconds)
        return None
    except urllib.error.HTTPError as exc:
        log.warning("vLLM HTTP error %s for %s", exc.code, endpoint)
        return None
    except Exception as exc:  # noqa: BLE001
        log.warning("vLLM request failed: %s", exc)
        return None
