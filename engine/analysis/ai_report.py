"""Generate an AI-written advisory report from an existing metrics.json."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from engine.core.config import AppConfig

log = logging.getLogger(__name__)

_ADVISORY_HEADER = (
    "> ⚠️ AI-generated summary — advisory only. "
    "Numeric scores come from static analysis.\n"
)


def generate_report(session_dir: Path, config: "AppConfig") -> Path | None:
    """Write ``ai_report.md`` in *session_dir* from its ``metrics.json``.

    Returns the path to the written file, or None when AI is disabled /
    unavailable / fails. Never raises to the caller.
    """
    if not config.analysis.enable_ai:
        log.debug("AI report skipped: enable_ai = false")
        return None

    try:
        return _generate(session_dir, config)
    except Exception as exc:  # noqa: BLE001
        log.warning("AI report generation failed unexpectedly: %s", exc)
        return None


# ── internal ──────────────────────────────────────────────────────────────────


def _generate(session_dir: Path, config: "AppConfig") -> Path | None:
    from ai.health import is_vllm_reachable

    if not is_vllm_reachable(config.ai.health_check_url):
        log.warning("vLLM not reachable — skipping AI report")
        return None

    metrics_path = session_dir / "metrics.json"
    if not metrics_path.is_file():
        log.warning("ai_report: metrics.json not found in %s", session_dir)
        return None

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    # Support single-player and multi-player metrics.json shapes
    if "players" in metrics:
        blocks: list[tuple[str, dict[str, Any]]] = list(metrics["players"].items())
    else:
        pid = metrics.get("gameplay", {}).get("player_id", "student")
        blocks = [(pid, metrics)]

    sections: list[str] = [_ADVISORY_HEADER]

    from ai import client as ai_client
    from ai.prompts import SYSTEM_PROMPT, build_user_prompt

    for player_id, block in blocks:
        prompt_kwargs = _extract_prompt_kwargs(block)
        user_prompt = build_user_prompt(**prompt_kwargs)
        response = ai_client.complete(SYSTEM_PROMPT, user_prompt, config)

        if response is None:
            log.warning("AI summary unavailable for player '%s' — took too long or offline", player_id)
            response = "_AI summary unavailable — vLLM timed out or went offline._"

        if len(blocks) > 1:
            sections.append(f"## Player: {player_id}\n")
        sections.append(response.strip())
        sections.append("")

    report_path = session_dir / "ai_report.md"
    report_path.write_text("\n".join(sections), encoding="utf-8")
    log.info("AI report written to %s", report_path)
    return report_path


def _extract_prompt_kwargs(block: dict[str, Any]) -> dict:
    scores = block.get("scores", {})
    gameplay_score = scores.get("gameplay", 0)
    code_quality_score = scores.get("code_quality", 0)
    final_score = scores.get("final", 0)

    feedback_items: list[str] = block.get("feedback", [])

    # Collect top Ruff violations from static metrics
    static = block.get("static", {})
    ruff_violations: dict[str, int] = static.get("ruff_violations", {})
    top_ruff = sorted(ruff_violations.items(), key=lambda kv: -kv[1])[:3]

    # Turn count from runtime
    runtime = block.get("runtime", {})
    turn_count = runtime.get("total_turns", 0)

    # Scenario name from gameplay section
    gameplay = block.get("gameplay", {})
    scenario_name = gameplay.get("scenario_id", "resource_wars")

    return {
        "scenario_name": scenario_name,
        "turn_count": turn_count,
        "gameplay_score": gameplay_score,
        "code_quality_score": code_quality_score,
        "final_score": final_score,
        "feedback_items": feedback_items,
        "top_ruff_violations": top_ruff,
    }
