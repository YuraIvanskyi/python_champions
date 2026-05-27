"""Load per-scenario scoring weights from scenario.toml."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from engine.paths import resource_path

SCENARIOS_ROOT = resource_path("scenarios")


@dataclass(frozen=True)
class ScoringWeights:
    gameplay_weight: float = 0.7
    code_weight: float = 0.3
    score_threshold: int = 15


def load_scoring_weights(scenario_id: str) -> ScoringWeights:
    scenario_dir = SCENARIOS_ROOT / scenario_id
    toml_path = scenario_dir / "scenario.toml"
    if not toml_path.is_file():
        return ScoringWeights()

    with toml_path.open("rb") as handle:
        data = tomllib.load(handle)

    scoring = data.get("scoring", {})
    scenario = data.get("scenario", {})
    threshold = int(
        scoring.get("score_threshold", scenario.get("score_threshold", 15))
    )
    return ScoringWeights(
        gameplay_weight=float(scoring.get("gameplay_weight", 0.7)),
        code_weight=float(scoring.get("code_weight", 0.3)),
        score_threshold=threshold,
    )
