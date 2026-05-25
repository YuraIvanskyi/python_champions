"""Tests for movement-based feedback template rules."""

from __future__ import annotations

from engine.analysis.feedback import generate_feedback_items
from engine.analysis.movement import MovementConfig


def _static_empty() -> dict:
    return {
        "ruff": [],
        "functions": [],
        "max_complexity": 0,
        "max_nesting_depth": 0,
        "max_function_lines": 0,
        "unused_names": [],
        "forbidden_constructs": [],
        "ast_error": None,
        "movement": {
            "no_walkable_check": False,
            "constant_action_return": False,
            "no_target_logic": False,
            "missing_fallback": False,
            "make_turn_line": None,
        },
    }


def _runtime_empty() -> dict:
    return {
        "turn_times_ms": [],
        "avg_turn_time_ms": 0.0,
        "max_turn_time_ms": 0.0,
        "timeout_count": 0,
        "crash_count": 0,
        "invalid_action_count": 0,
        "total_turns": 20,
    }


def _movement(*, analyzed: bool = True, **kwargs) -> dict:
    base = {
        "analyzed": analyzed,
        "blocked_move_ratio": 0.0,
        "max_consecutive_same_action": 0,
        "wait_ratio": 0.0,
        "position_revisit_count": 0,
        "stuck_episodes": 0,
        "oscillation_episodes": 0,
        "score_stall_turns": 0,
        "unique_positions_ratio": 1.0,
        "worst_stuck_turn_range": [],
    }
    base.update(kwargs)
    return base


CFG = MovementConfig(
    stuck_window_turns=10,
    stuck_revisit_threshold=3,
    consecutive_action_warn=8,
    blocked_ratio_warn=0.35,
    score_stall_warn=12,
    oscillation_min_cycles=3,
    min_turns_for_analysis=5,
)


# ---------------------------------------------------------------------------
# Movement feedback triggers
# ---------------------------------------------------------------------------

def test_stuck_episode_produces_logic_item() -> None:
    mv = _movement(stuck_episodes=1, worst_stuck_turn_range=[5, 14])
    items = generate_feedback_items(
        static=_static_empty(),
        runtime=_runtime_empty(),
        movement=mv,
        movement_cfg=CFG,
    )
    titles = [it.title for it in items]
    assert any("Stuck" in t for t in titles)
    stuck_item = next(it for it in items if "Stuck" in it.title)
    assert stuck_item.category == "logic"
    assert "5" in stuck_item.message or "14" in stuck_item.message  # range included


def test_oscillation_produces_logic_item() -> None:
    mv = _movement(oscillation_episodes=2)
    items = generate_feedback_items(
        static=_static_empty(), runtime=_runtime_empty(), movement=mv, movement_cfg=CFG
    )
    assert any("Bouncing" in it.title or "ping-pong" in it.message.lower() for it in items)


def test_high_blocked_ratio_produces_item() -> None:
    mv = _movement(blocked_move_ratio=0.5)
    items = generate_feedback_items(
        static=_static_empty(), runtime=_runtime_empty(), movement=mv, movement_cfg=CFG
    )
    assert any("blocked" in it.title.lower() for it in items)
    blocked_item = next(it for it in items if "blocked" in it.title.lower())
    assert "50%" in blocked_item.message


def test_consecutive_same_action_produces_item() -> None:
    mv = _movement(max_consecutive_same_action=12)
    items = generate_feedback_items(
        static=_static_empty(), runtime=_runtime_empty(), movement=mv, movement_cfg=CFG
    )
    assert any("Repeating" in it.title for it in items)
    repeat_item = next(it for it in items if "Repeating" in it.title)
    assert "12" in repeat_item.message


def test_score_stall_produces_item() -> None:
    mv = _movement(score_stall_turns=15)
    items = generate_feedback_items(
        static=_static_empty(), runtime=_runtime_empty(), movement=mv, movement_cfg=CFG
    )
    assert any("progress" in it.title.lower() or "scoring" in it.title.lower() for it in items)


def test_no_walkable_plus_blocked_produces_combined_message() -> None:
    static = _static_empty()
    static["movement"]["no_walkable_check"] = True
    mv = _movement(blocked_move_ratio=0.5)
    items = generate_feedback_items(
        static=static, runtime=_runtime_empty(), movement=mv, movement_cfg=CFG
    )
    blocked_item = next((it for it in items if "blocked" in it.title.lower()), None)
    assert blocked_item is not None
    assert "is_walkable" in blocked_item.message.lower()


def test_constant_return_produces_logic_item() -> None:
    static = _static_empty()
    static["movement"]["constant_action_return"] = True
    mv = _movement()
    items = generate_feedback_items(
        static=static, runtime=_runtime_empty(), movement=mv, movement_cfg=CFG
    )
    assert any("decision" in it.title.lower() or "logic" in it.title.lower() for it in items)


def test_no_target_logic_produces_item() -> None:
    static = _static_empty()
    static["movement"]["no_target_logic"] = True
    mv = _movement()
    items = generate_feedback_items(
        static=static, runtime=_runtime_empty(), movement=mv, movement_cfg=CFG
    )
    assert any("goal" in it.title.lower() for it in items)


# ---------------------------------------------------------------------------
# Priority ordering
# ---------------------------------------------------------------------------

def test_movement_items_before_style_and_praise() -> None:
    """Stuck/blocked items must appear before style/praise cards."""
    static = _static_empty()
    static["ruff"] = [{"code": "E501", "line": 5, "message": "Line too long"}]
    mv = _movement(stuck_episodes=1, worst_stuck_turn_range=[1, 10])
    items = generate_feedback_items(
        static=static, runtime=_runtime_empty(), movement=mv, movement_cfg=CFG
    )
    categories = [it.category for it in items]
    logic_idx = next((i for i, c in enumerate(categories) if c == "logic"), len(categories))
    style_idx = next((i for i, c in enumerate(categories) if c == "style"), len(categories))
    assert logic_idx < style_idx, "Logic/movement items should come before style"


def test_no_movement_items_when_all_clean() -> None:
    """Clean bot with no issues gets praise, not movement warnings."""
    mv = _movement()  # all zeros, analyzed=True
    items = generate_feedback_items(
        static=_static_empty(), runtime=_runtime_empty(), movement=mv, movement_cfg=CFG
    )
    categories = {it.category for it in items}
    # Should get praise; no logic movement warnings
    assert "praise" in categories
    logic_items = [it for it in items if it.category == "logic"]
    assert not logic_items


# ---------------------------------------------------------------------------
# Static-only fallback (no replay)
# ---------------------------------------------------------------------------

def test_static_only_constant_return_when_no_replay() -> None:
    """When analyzed=False, static flags still generate feedback."""
    static = _static_empty()
    static["movement"]["constant_action_return"] = True
    mv = _movement(analyzed=False)
    items = generate_feedback_items(
        static=static, runtime=_runtime_empty(), movement=mv, movement_cfg=CFG
    )
    assert any("decision" in it.title.lower() or "logic" in it.title.lower() for it in items)


def test_no_movement_warnings_when_not_analyzed_and_clean() -> None:
    """analyzed=False + no static flags → no logic movement cards."""
    mv = _movement(analyzed=False)
    items = generate_feedback_items(
        static=_static_empty(), runtime=_runtime_empty(), movement=mv, movement_cfg=CFG
    )
    logic_items = [it for it in items if it.category == "logic"]
    assert not logic_items
