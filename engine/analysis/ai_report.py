"""Generate an AI-written advisory report from an existing metrics.json."""

from __future__ import annotations

import json
import logging
from collections import Counter
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
        log.warning("AI not reachable — skipping AI report")
        return None

    metrics_path = session_dir / "metrics.json"
    if not metrics_path.is_file():
        log.warning("ai_report: metrics.json not found in %s", session_dir)
        return None

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    replay  = _load_replay(session_dir)

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
        prompt_kwargs = _extract_prompt_kwargs(block, player_id=player_id, replay=replay)
        user_prompt = build_user_prompt(**prompt_kwargs)
        response = ai_client.complete(SYSTEM_PROMPT, user_prompt, config)

        if response is None:
            log.warning("AI summary unavailable for '%s' — timed out or offline", player_id)
            response = "_AI summary unavailable — AI timed out or went offline._"

        if len(blocks) > 1:
            sections.append(f"## Player: {player_id}\n")
        sections.append(response.strip())
        sections.append("")

    report_path = session_dir / "ai_report.md"
    report_path.write_text("\n".join(sections), encoding="utf-8")
    log.info("AI report written to %s", report_path)
    return report_path


def _load_replay(session_dir: Path) -> dict[str, Any]:
    path = session_dir / "replay.json"
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
    return {}


def _action_distribution(replay: dict[str, Any], player_id: str) -> dict[str, int]:
    """Count how often each action appeared across all turns for this player."""
    counts: Counter[str] = Counter()
    for turn in replay.get("turns", []):
        action = turn.get("actions", {}).get(player_id)
        if action:
            counts[action] += 1
    return dict(counts)


def _score_trajectory(replay: dict[str, Any], player_id: str) -> list[tuple[int, int]]:
    """Return [(turn_number, cumulative_score)] for every turn."""
    result: list[tuple[int, int]] = []
    for turn in replay.get("turns", []):
        t = turn.get("turn", 0)
        s = turn.get("scores", {}).get(player_id, 0)
        result.append((t, s))
    return result


def _extract_prompt_kwargs(
    block: dict[str, Any],
    *,
    player_id: str,
    replay: dict[str, Any],
) -> dict:
    scores            = block.get("scores", {})
    gameplay_score    = scores.get("gameplay", 0)
    code_quality_score = scores.get("code_quality", 0)
    final_score       = scores.get("final", 0)

    feedback_items: list[str] = block.get("feedback", [])

    # Static metrics
    static            = block.get("static", {})
    ruff_list         = static.get("ruff", [])  # list of {code, line, message}
    ruff_counts: Counter[str] = Counter(r["code"] for r in ruff_list)
    top_ruff          = ruff_counts.most_common(3)

    funcs             = static.get("functions", [])
    main_func         = funcs[0] if funcs else {}
    complexity_rank   = main_func.get("complexity_rank", "?")
    function_line_count = main_func.get("line_count", 0)
    max_nesting_depth = static.get("max_nesting_depth", 0)

    # Runtime metrics
    runtime           = block.get("runtime", {})
    turn_count        = runtime.get("total_turns", 0)
    avg_turn_ms       = round(runtime.get("avg_turn_time_ms", 0.0), 2)
    timeout_count     = runtime.get("timeout_count", 0)
    crash_count       = runtime.get("crash_count", 0)
    invalid_action_count = runtime.get("invalid_action_count", 0)

    # Gameplay context
    gameplay          = block.get("gameplay", {})
    scenario_name     = gameplay.get("scenario_id", "resource_wars")
    resources_gathered = gameplay.get("resources", 0)
    score_threshold   = gameplay.get("score_threshold", 0)

    # Replay-derived game flow
    action_dist       = _action_distribution(replay, player_id)
    score_traj        = _score_trajectory(replay, player_id)

    # Movement analysis
    movement          = block.get("movement", {})
    static_movement   = block.get("static", {}).get("movement", {})

    return {
        "scenario_name":       scenario_name,
        "turn_count":          turn_count,
        "gameplay_score":      gameplay_score,
        "code_quality_score":  code_quality_score,
        "final_score":         final_score,
        "resources_gathered":  resources_gathered,
        "score_threshold":     score_threshold,
        "feedback_items":      feedback_items,
        "top_ruff_violations": top_ruff,
        "action_distribution": action_dist,
        "score_trajectory":    score_traj,
        "avg_turn_ms":         avg_turn_ms,
        "timeout_count":       timeout_count,
        "crash_count":         crash_count,
        "invalid_action_count": invalid_action_count,
        "complexity_rank":     complexity_rank,
        "max_nesting_depth":   max_nesting_depth,
        "function_line_count": function_line_count,
        "movement":            movement,
        "static_movement":     static_movement,
    }
