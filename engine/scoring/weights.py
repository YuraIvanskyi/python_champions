"""Load per-scenario scoring weights from scenario.toml."""

from __future__ import annotations

from dataclasses import dataclass

from engine.core.config_io import load_scenario_toml


@dataclass(frozen=True)
class ScoringWeights:
    gameplay_weight: float = 0.7
    code_weight: float = 0.3
    score_threshold: int = 15


def load_scoring_weights(scenario_id: str) -> ScoringWeights:
    try:
        data = load_scenario_toml(scenario_id)
    except OSError:
        return ScoringWeights()

    scoring = data.get("scoring", {})
    scenario = data.get("scenario", {})
    threshold = int(
        scoring.get("score_threshold", scenario.get("score_threshold", 15))
    )
    gameplay_weight = float(scoring.get("gameplay_weight", 0.7))
    code_weight = float(scoring.get("code_weight", 0.3))

    if gameplay_weight < 0 or code_weight < 0:
        raise ValueError(f"Scoring weights must be non-negative for {scenario_id}")
    total = gameplay_weight + code_weight
    if abs(total - 1.0) > 0.001:
        raise ValueError(
            f"Scoring weights must sum to 1.0 for {scenario_id} (got {total})"
        )

    return ScoringWeights(
        gameplay_weight=gameplay_weight,
        code_weight=code_weight,
        score_threshold=threshold,
    )
