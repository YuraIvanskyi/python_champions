"""Unit tests for the replay-based movement analyzer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.analysis.movement import (
    MovementConfig,
    MovementMetrics,
    analyze_movement,
    _compute_metrics,
    _max_consecutive_action,
    _detect_oscillation,
    _detect_stuck,
    _longest_score_stall,
    _revisit_count,
)


# ---------------------------------------------------------------------------
# Helpers to build minimal replay structures
# ---------------------------------------------------------------------------

def _make_replay(
    turns: list[dict],
    scenario: str = "resource_wars",
    seed: int = 42,
    player_ids: list[str] | None = None,
) -> dict:
    pids = player_ids or ["student", "opponent"]
    final = {pid: turns[-1].get("scores", {}).get(pid, 0) for pid in pids} if turns else {p: 0 for p in pids}
    return {
        "schema_version": 2,
        "seed": seed,
        "scenario": scenario,
        "player_ids": pids,
        "turns": turns,
        "final_scores": final,
    }


def _turn(n: int, action: str, *, pid: str = "student", score: int = 0, events: list[str] | None = None) -> dict:
    return {
        "turn": n,
        "actions": {pid: action, "opponent": "WAIT"},
        "scores": {pid: score, "opponent": 0},
        "events": events or [],
    }


# ---------------------------------------------------------------------------
# Low-level metric helpers
# ---------------------------------------------------------------------------

def test_max_consecutive_action_streak() -> None:
    turns = [_turn(i, "MOVE_RIGHT" if i <= 5 else "GATHER") for i in range(1, 11)]
    result = _max_consecutive_action(turns, "student")
    assert result == 5


def test_max_consecutive_action_no_repeat() -> None:
    actions = ["MOVE_RIGHT", "MOVE_LEFT", "MOVE_UP", "GATHER"]
    turns = [_turn(i, a) for i, a in enumerate(actions, 1)]
    assert _max_consecutive_action(turns, "student") == 1


def test_revisit_count() -> None:
    positions = [(1, 1), (1, 2), (1, 1), (1, 3), (1, 1)]
    assert _revisit_count(positions) == 2


def test_detect_oscillation_found() -> None:
    # A→B→A→B→A→B → plenty of cycles
    positions = [(0, 0), (1, 0)] * 5
    cfg = MovementConfig(oscillation_min_cycles=2)
    assert _detect_oscillation(positions, cfg.oscillation_min_cycles) >= 1


def test_detect_oscillation_not_enough_cycles() -> None:
    positions = [(0, 0), (1, 0), (0, 0), (1, 0)]
    # Only 1 cycle — needs 3 minimum
    assert _detect_oscillation(positions, 3) == 0


def test_detect_stuck_episode() -> None:
    # Same position repeated many times with flat score
    positions: list[tuple[int, int] | None] = [(2, 3)] * 12
    scores = [(i, 0) for i in range(1, 13)]
    cfg = MovementConfig(stuck_window_turns=10, stuck_revisit_threshold=3)
    episodes, worst_range = _detect_stuck(positions, scores, cfg)
    assert episodes >= 1
    assert len(worst_range) == 2


def test_detect_stuck_no_episode_when_score_rises() -> None:
    positions: list[tuple[int, int] | None] = [(2, 3)] * 12
    scores = [(i, i) for i in range(1, 13)]  # score increases every turn
    cfg = MovementConfig(stuck_window_turns=10, stuck_revisit_threshold=3)
    episodes, _ = _detect_stuck(positions, scores, cfg)
    assert episodes == 0


def test_longest_score_stall_moving() -> None:
    # Bot moves (MOVE_RIGHT events) for 15 turns without scoring
    turns = []
    for i in range(1, 20):
        score = 1 if i >= 16 else 0
        turns.append({
            "turn": i,
            "actions": {"student": "MOVE_RIGHT"},
            "scores": {"student": score},
            "events": ["student_moved"],
        })
    stall = _longest_score_stall(turns, "student")
    assert stall >= 14


def test_longest_score_stall_waiting_not_counted() -> None:
    # Bot waits every turn — wait turns should NOT contribute to movement stall
    turns = [
        {
            "turn": i,
            "actions": {"student": "WAIT"},
            "scores": {"student": 0},
            "events": ["student_waited"],
        }
        for i in range(1, 20)
    ]
    stall = _longest_score_stall(turns, "student")
    assert stall == 0


# ---------------------------------------------------------------------------
# Full compute_metrics integration
# ---------------------------------------------------------------------------

def test_compute_metrics_all_blocked() -> None:
    """Bot always walks into a wall: high blocked ratio, no movement events."""
    turns = []
    for i in range(1, 21):
        turns.append({
            "turn": i,
            "actions": {"student": "MOVE_RIGHT"},
            "scores": {"student": 0},
            "events": ["student_blocked"],
        })
    cfg = MovementConfig(min_turns_for_analysis=5)
    m = _compute_metrics(turns, [], "student", cfg)
    assert m.blocked_move_ratio == 1.0


def test_compute_metrics_all_moved() -> None:
    turns = []
    for i in range(1, 21):
        turns.append({
            "turn": i,
            "actions": {"student": "MOVE_RIGHT"},
            "scores": {"student": i},
            "events": ["student_moved"],
        })
    cfg = MovementConfig(min_turns_for_analysis=5)
    m = _compute_metrics(turns, [], "student", cfg)
    assert m.blocked_move_ratio == 0.0
    assert m.wait_ratio == 0.0


def test_compute_metrics_high_wait_ratio() -> None:
    turns = [_turn(i, "WAIT", events=["student_waited"]) for i in range(1, 21)]
    cfg = MovementConfig()
    m = _compute_metrics(turns, [], "student", cfg)
    assert m.wait_ratio > 0.9


# ---------------------------------------------------------------------------
# analyze_movement with missing replay (graceful degradation)
# ---------------------------------------------------------------------------

def test_analyze_movement_no_replay(tmp_path: Path) -> None:
    """No replay.json → returns unanalyzed zeroed metrics."""
    result = analyze_movement(tmp_path, "student")
    assert isinstance(result, MovementMetrics)
    assert result.analyzed is False
    assert result.stuck_episodes == 0


def test_analyze_movement_too_few_turns(tmp_path: Path) -> None:
    replay = _make_replay([_turn(1, "WAIT")])
    (tmp_path / "replay.json").write_text(json.dumps(replay), encoding="utf-8")
    cfg = MovementConfig(min_turns_for_analysis=5)
    result = analyze_movement(tmp_path, "student", cfg=cfg)
    assert result.analyzed is False


def test_analyze_movement_returns_dict_via_to_dict() -> None:
    m = MovementMetrics(analyzed=True, stuck_episodes=2, blocked_move_ratio=0.4)
    d = m.to_dict()
    assert d["stuck_episodes"] == 2
    assert d["blocked_move_ratio"] == pytest.approx(0.4)
    assert d["analyzed"] is True
