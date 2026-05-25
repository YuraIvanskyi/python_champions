"""Combined final score from gameplay and code quality."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.scoring.code_quality import compute_code_quality
from engine.scoring.gameplay import compute_gameplay_score
from engine.scoring.weights import ScoringWeights

# If the bot crashed at runtime its code quality is capped at this value,
# regardless of what static analysis computed.  A bot that crashes is
# fundamentally broken even if its style is otherwise clean.
_CRASH_QUALITY_CAP = 50


@dataclass(frozen=True)
class ScoreBreakdown:
    gameplay: int
    code_quality: int
    final: float
    gameplay_weight: float
    code_weight: float
    crash_penalty_applied: bool = False


def compute_scores(
    *,
    final_scores: dict[str, int],
    static: dict,
    weights: ScoringWeights,
    player_id: str = "student",
    runtime: dict[str, Any] | None = None,
) -> ScoreBreakdown:
    gameplay = compute_gameplay_score(
        final_scores,
        player_id=player_id,
        score_threshold=weights.score_threshold,
    )
    code_quality = compute_code_quality(static)

    crash_count = int((runtime or {}).get("crash_count", 0))
    crash_penalty = crash_count > 0 and code_quality > _CRASH_QUALITY_CAP
    if crash_penalty:
        code_quality = _CRASH_QUALITY_CAP

    final = gameplay * weights.gameplay_weight + code_quality * weights.code_weight
    return ScoreBreakdown(
        gameplay=gameplay,
        code_quality=code_quality,
        final=round(final, 1),
        gameplay_weight=weights.gameplay_weight,
        code_weight=weights.code_weight,
        crash_penalty_applied=crash_penalty,
    )
