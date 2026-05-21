"""Combined scoring respects configurable weights."""

from engine.scoring.combined import compute_scores
from engine.scoring.weights import ScoringWeights


def test_combined_score_default_weights() -> None:
    weights = ScoringWeights(gameplay_weight=0.7, code_weight=0.3, score_threshold=15)
    breakdown = compute_scores(
        final_scores={"student": 15, "opponent": 0},
        static={
            "max_complexity": 1,
            "max_nesting_depth": 0,
            "max_function_lines": 5,
            "ruff": [],
            "forbidden_constructs": [],
            "unused_names": [],
            "functions": [],
        },
        weights=weights,
    )
    assert breakdown.gameplay == 100
    assert breakdown.code_quality == 100
    assert breakdown.final == 100.0


def test_combined_score_custom_weights() -> None:
    weights = ScoringWeights(gameplay_weight=0.5, code_weight=0.5, score_threshold=10)
    breakdown = compute_scores(
        final_scores={"student": 5, "opponent": 0},
        static={
            "max_complexity": 12,
            "max_nesting_depth": 5,
            "max_function_lines": 80,
            "ruff": [{"code": "F401"}],
            "forbidden_constructs": [],
            "unused_names": [],
            "functions": [],
        },
        weights=weights,
    )
    assert breakdown.gameplay == 50
    assert breakdown.code_quality < 100
    expected = breakdown.gameplay * 0.5 + breakdown.code_quality * 0.5
    assert breakdown.final == round(expected, 1)
