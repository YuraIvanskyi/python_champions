"""Combined scoring respects configurable weights."""

from engine.scoring.combined import _CRASH_QUALITY_CAP, compute_scores
from engine.scoring.weights import ScoringWeights

_CLEAN_STATIC = {
    "max_complexity": 1,
    "max_nesting_depth": 0,
    "max_function_lines": 5,
    "ruff": [],
    "forbidden_constructs": [],
    "unused_names": [],
    "functions": [],
    "ast_error": None,
}

_WEIGHTS_70_30 = ScoringWeights(gameplay_weight=0.7, code_weight=0.3, score_threshold=15)


def test_combined_score_default_weights() -> None:
    breakdown = compute_scores(
        final_scores={"student": 15, "opponent": 0},
        static=_CLEAN_STATIC,
        weights=_WEIGHTS_70_30,
    )
    assert breakdown.gameplay == 100
    assert breakdown.code_quality == 100
    assert breakdown.final == 100.0
    assert breakdown.crash_penalty_applied is False


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


def test_crash_caps_code_quality_at_50() -> None:
    """A bot that crashes must not score above 50 on code quality."""
    breakdown = compute_scores(
        final_scores={"student": 15, "opponent": 0},
        static=_CLEAN_STATIC,
        weights=_WEIGHTS_70_30,
        runtime={"crash_count": 1},
    )
    assert breakdown.code_quality == _CRASH_QUALITY_CAP
    assert breakdown.crash_penalty_applied is True
    expected = 100 * 0.7 + _CRASH_QUALITY_CAP * 0.3
    assert breakdown.final == round(expected, 1)


def test_crash_cap_not_applied_when_quality_already_low() -> None:
    """Cap only kicks in when the computed quality would exceed 50."""
    breakdown = compute_scores(
        final_scores={"student": 0, "opponent": 0},
        static={
            "max_complexity": 12,
            "max_nesting_depth": 5,
            "max_function_lines": 80,
            "ruff": [{"code": "F401"}] * 8,
            "forbidden_constructs": [],
            "unused_names": [],
            "functions": [],
        },
        weights=_WEIGHTS_70_30,
        runtime={"crash_count": 2},
    )
    # Static score is already <= 50, cap should not apply
    assert breakdown.crash_penalty_applied is False
    assert breakdown.code_quality <= _CRASH_QUALITY_CAP


def test_no_crash_no_cap() -> None:
    """Without a crash the quality score is unrestricted."""
    breakdown = compute_scores(
        final_scores={"student": 15, "opponent": 0},
        static=_CLEAN_STATIC,
        weights=_WEIGHTS_70_30,
        runtime={"crash_count": 0},
    )
    assert breakdown.code_quality == 100
    assert breakdown.crash_penalty_applied is False
