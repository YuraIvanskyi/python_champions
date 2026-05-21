"""Combined final score from gameplay and code quality."""

from __future__ import annotations

from dataclasses import dataclass

from engine.scoring.code_quality import compute_code_quality
from engine.scoring.gameplay import compute_gameplay_score
from engine.scoring.weights import ScoringWeights


@dataclass(frozen=True)
class ScoreBreakdown:
    gameplay: int
    code_quality: int
    final: float
    gameplay_weight: float
    code_weight: float


def compute_scores(
    *,
    final_scores: dict[str, int],
    static: dict,
    weights: ScoringWeights,
    player_id: str = "student",
) -> ScoreBreakdown:
    gameplay = compute_gameplay_score(
        final_scores,
        player_id=player_id,
        score_threshold=weights.score_threshold,
    )
    code_quality = compute_code_quality(static)
    final = gameplay * weights.gameplay_weight + code_quality * weights.code_weight
    return ScoreBreakdown(
        gameplay=gameplay,
        code_quality=code_quality,
        final=round(final, 1),
        gameplay_weight=weights.gameplay_weight,
        code_weight=weights.code_weight,
    )
