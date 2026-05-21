"""Normalize scenario raw scores to a 0–100 gameplay score."""

from __future__ import annotations


def compute_gameplay_score(
    final_scores: dict[str, int],
    *,
    player_id: str = "student",
    score_threshold: int,
) -> int:
    """Map student resource score to 0–100 using scenario victory threshold."""
    raw = int(final_scores.get(player_id, 0))
    if score_threshold <= 0:
        return min(100, raw)
    normalized = int(round((raw / score_threshold) * 100))
    return max(0, min(100, normalized))
