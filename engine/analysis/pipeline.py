"""Post-session analysis: static + runtime → metrics.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.analysis.feedback import generate_feedback, generate_feedback_items
from engine.analysis.runtime import RuntimeCollector
from engine.analysis.static import analyze_static, static_to_dict
from engine.core.config import AppConfig
from engine.scoring.combined import compute_scores
from engine.scoring.weights import load_scoring_weights


def build_metrics(
    *,
    bot_path: Path,
    config: AppConfig,
    final_scores: dict[str, int],
    scenario_id: str,
    runtime_collector: RuntimeCollector | None = None,
    player_id: str = "student",
) -> dict[str, Any]:
    static_metrics = analyze_static(
        bot_path,
        ruff_select=config.analysis.ruff_select,
        forbidden_names=config.analysis.forbidden_imports,
        enabled=config.analysis.enable_static_analysis,
    )
    static_dict = static_to_dict(static_metrics)

    runtime_dict = (
        runtime_collector.to_dict()
        if runtime_collector is not None
        else {
            "turn_times_ms": [],
            "avg_turn_time_ms": 0.0,
            "max_turn_time_ms": 0.0,
            "timeout_count": 0,
            "crash_count": 0,
            "invalid_action_count": 0,
            "total_turns": 0,
        }
    )

    weights = load_scoring_weights(scenario_id)
    breakdown = compute_scores(
        final_scores=final_scores,
        static=static_dict,
        weights=weights,
        player_id=player_id,
    )

    gameplay_detail = {
        "raw_scores": final_scores,
        "player_id": player_id,
        "resources": final_scores.get(player_id, 0),
        "normalized": breakdown.gameplay,
        "score_threshold": weights.score_threshold,
    }

    items = generate_feedback_items(static=static_dict, runtime=runtime_dict)
    feedback = [item.message for item in items]

    return {
        "gameplay": gameplay_detail,
        "static": static_dict,
        "runtime": runtime_dict,
        "scores": {
            "gameplay": breakdown.gameplay,
            "code_quality": breakdown.code_quality,
            "final": breakdown.final,
            "weights": {
                "gameplay": breakdown.gameplay_weight,
                "code": breakdown.code_weight,
            },
        },
        "feedback": feedback,
        "feedback_items": [item.to_dict() for item in items],
    }


def write_metrics(session_dir: Path, metrics: dict[str, Any]) -> Path:
    path = session_dir / "metrics.json"
    path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def run_analysis_for_session(
    session_dir: Path,
    *,
    bot_path: Path,
    config: AppConfig,
    final_scores: dict[str, int],
    scenario_id: str,
    runtime_collector: RuntimeCollector | None = None,
    player_id: str = "student",
) -> dict[str, Any]:
    """Analyze one bot and merge into session metrics.json."""
    per_player = _load_or_init_session_metrics(session_dir)
    per_player[player_id] = build_metrics(
        bot_path=bot_path,
        config=config,
        final_scores=final_scores,
        scenario_id=scenario_id,
        runtime_collector=runtime_collector,
        player_id=player_id,
    )
    payload = _session_metrics_payload(per_player)
    write_metrics(session_dir, payload)
    return per_player[player_id]


def _load_or_init_session_metrics(session_dir: Path) -> dict[str, dict[str, Any]]:
    path = session_dir / "metrics.json"
    if not path.is_file():
        return {}
    existing = json.loads(path.read_text(encoding="utf-8"))
    if "players" in existing:
        return dict(existing["players"])
    if "scores" in existing:
        pid = existing.get("gameplay", {}).get("player_id", "student")
        return {pid: existing}
    return {}


def _session_metrics_payload(per_player: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if len(per_player) == 1:
        return next(iter(per_player.values()))
    return {"players": per_player}


def print_analysis_summary(metrics: dict[str, Any]) -> None:
    """Print top feedback items and final score for CLI beginners."""
    if "players" in metrics:
        for pid, block in metrics["players"].items():
            print(f"--- {pid} ---")
            _print_single_summary(block)
        return
    _print_single_summary(metrics)


def _print_single_summary(metrics: dict[str, Any]) -> None:
    scores = metrics.get("scores", {})
    final = scores.get("final", 0)
    gameplay = scores.get("gameplay", 0)
    code_quality = scores.get("code_quality", 0)
    print(f"Final score: {final} (gameplay {gameplay}, code quality {code_quality})")

    feedback: list[str] = metrics.get("feedback", [])
    if not feedback:
        return
    print("Feedback:")
    for item in feedback[:3]:
        print(f"  • {item}")
