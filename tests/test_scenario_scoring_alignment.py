"""Each scenario's match scores must align with analysis score_threshold."""

from __future__ import annotations

from engine.scoring.combined import compute_scores
from engine.scoring.gameplay import compute_gameplay_score
from engine.scoring.weights import load_scoring_weights
from scenarios.boss_fight.game import BossFightScenario
from scenarios.mana_pools.game import ManaPoolsScenario
from scenarios.resource_wars.game import ResourceWarsScenario

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


def test_resource_wars_threshold_matches_victory_target() -> None:
    """Raw resource counts; reaching score_threshold is a perfect gameplay score."""
    scenario = ResourceWarsScenario(1, player_ids=["a", "b"])
    scenario.setup()
    weights = load_scoring_weights("resource_wars")

    assert weights.score_threshold == scenario._score_threshold == 15

    mid = compute_gameplay_score({"a": 8}, player_id="a", score_threshold=weights.score_threshold)
    perfect = compute_gameplay_score({"b": 15}, player_id="b", score_threshold=weights.score_threshold)
    assert mid == 53
    assert perfect == 100


def test_boss_fight_threshold_matches_percent_scores() -> None:
    """Win scores are damage shares 0–100; loss scores cap below 100."""
    weights = load_scoring_weights("boss_fight")
    assert weights.score_threshold == 100

    win = BossFightScenario(0, player_ids=["a", "b"])
    win.setup()
    win._damage_dealt = {"a": 60, "b": 40}
    win._boss_hp = 0
    win._finished = True
    win_scores = win.calculate_score()
    assert win_scores == {"a": 60, "b": 40}

    a_win = compute_scores(
        final_scores=win_scores, static=_CLEAN_STATIC, weights=weights, player_id="a",
    )
    b_win = compute_scores(
        final_scores=win_scores, static=_CLEAN_STATIC, weights=weights, player_id="b",
    )
    assert a_win.gameplay == 60
    assert b_win.gameplay == 40

    loss = BossFightScenario(0, player_ids=["solo"])
    loss.setup()
    loss._damage_dealt = {"solo": 10}
    loss._boss_hp = 5
    loss_scores = loss.calculate_score()
    assert loss_scores["solo"] <= 79

    solo_loss = compute_scores(
        final_scores=loss_scores, static=_CLEAN_STATIC, weights=weights, player_id="solo",
    )
    assert solo_loss.gameplay == loss_scores["solo"]


def test_mana_pools_threshold_matches_normalized_scores() -> None:
    """calculate_score() returns 0–100 mana share; analysis must not saturate early."""
    weights = load_scoring_weights("mana_pools")
    assert weights.score_threshold == 100

    scenario = ManaPoolsScenario(1, player_ids=["a", "b"])
    scenario.setup()
    scenario._energy = {"a": 62, "b": 100}
    match_scores = scenario.calculate_score()
    assert match_scores == {"a": 62, "b": 100}

    mid = compute_scores(
        final_scores=match_scores, static=_CLEAN_STATIC, weights=weights, player_id="a",
    )
    top = compute_scores(
        final_scores=match_scores, static=_CLEAN_STATIC, weights=weights, player_id="b",
    )
    assert mid.gameplay == 62
    assert top.gameplay == 100
    assert top.final > mid.final


def test_mid_range_scores_do_not_all_saturate_at_100() -> None:
    """Regression: wrong threshold makes unlike match scores look identical in analysis."""
    weights = load_scoring_weights("mana_pools")
    samples = [42, 62, 73, 100]
    gameplay_scores = [
        compute_gameplay_score({f"p{i}": s for i, s in enumerate(samples)}, player_id=f"p{i}", score_threshold=weights.score_threshold)
        for i, s in enumerate(samples)
    ]
    assert len(set(gameplay_scores)) == len(samples)
    assert gameplay_scores == samples
