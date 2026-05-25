"""Phase 4: Prompt content guard-rails."""

from __future__ import annotations

from ai.prompts import SYSTEM_PROMPT, build_user_prompt


def _sample_prompt(*, include_movement: bool = False) -> str:
    mv = (
        {
            "analyzed": True,
            "blocked_move_ratio": 0.42,
            "max_consecutive_same_action": 14,
            "wait_ratio": 0.05,
            "stuck_episodes": 2,
            "oscillation_episodes": 1,
            "score_stall_turns": 18,
            "unique_positions_ratio": 0.3,
            "worst_stuck_turn_range": [10, 19],
        }
        if include_movement
        else None
    )
    static_mv = (
        {"no_walkable_check": True, "constant_action_return": False}
        if include_movement
        else None
    )
    return build_user_prompt(
        scenario_name="resource_wars",
        turn_count=50,
        gameplay_score=72.0,
        code_quality_score=65.0,
        final_score=70.1,
        resources_gathered=8,
        score_threshold=15,
        feedback_items=["Avoid bare except clauses", "Add docstring to make_turn"],
        top_ruff_violations=[("E501", 3), ("F401", 2)],
        action_distribution={"GATHER": 10, "MOVE_RIGHT": 25, "MOVE_UP": 15},
        score_trajectory=[(1, 0), (10, 1), (25, 4), (50, 8)],
        avg_turn_ms=0.8,
        timeout_count=0,
        crash_count=0,
        invalid_action_count=0,
        complexity_rank="B",
        max_nesting_depth=3,
        function_line_count=28,
        movement=mv,
        static_movement=static_mv,
    )


def test_system_prompt_allows_tiny_code_examples() -> None:
    lower = SYSTEM_PROMPT.lower()
    assert "1" in lower and ("line" in lower or "example" in lower)

def test_system_prompt_forbids_full_solutions() -> None:
    lower = SYSTEM_PROMPT.lower()
    assert "do not generate full solutions" in lower or "not generate full solutions" in lower


def test_user_prompt_contains_scores() -> None:
    prompt = _sample_prompt()
    assert "72" in prompt or "72.0" in prompt
    assert "65" in prompt or "65.0" in prompt


def test_user_prompt_contains_feedback_items() -> None:
    prompt = _sample_prompt()
    assert "bare except" in prompt.lower()
    assert "docstring" in prompt.lower()


def test_user_prompt_contains_ruff_violations() -> None:
    prompt = _sample_prompt()
    assert "E501" in prompt
    assert "F401" in prompt


def test_user_prompt_contains_scenario_name() -> None:
    prompt = _sample_prompt()
    assert "resource_wars" in prompt


def test_user_prompt_contains_action_distribution() -> None:
    prompt = _sample_prompt()
    assert "GATHER" in prompt
    assert "MOVE_RIGHT" in prompt


def test_user_prompt_contains_score_trajectory() -> None:
    prompt = _sample_prompt()
    # Should mention when first resource was gathered
    assert "first resource" in prompt.lower() or "turn 10" in prompt


def test_user_prompt_contains_complexity_rank() -> None:
    prompt = _sample_prompt()
    assert "complexity rank" in prompt.lower() or "rank B" in prompt or " B" in prompt


def test_user_prompt_no_engine_class_names() -> None:
    """Ensure no engine internals leak into the user prompt."""
    prompt = _sample_prompt()
    forbidden = ["LiveGame", "ResourceWarsScenario", "AppConfig", "TurnResult", "RunResult"]
    for name in forbidden:
        assert name not in prompt, f"Engine class '{name}' leaked into user prompt"


def test_user_prompt_no_raw_source_code() -> None:
    """The user prompt must not contain Python source code snippets."""
    prompt = _sample_prompt()
    # These keywords indicate raw source inclusion
    source_indicators = ["def make_turn", "import ", "class StudentBot"]
    for indicator in source_indicators:
        assert indicator not in prompt, f"Source snippet leaked: {indicator!r}"


def test_user_prompt_movement_section_included() -> None:
    prompt = _sample_prompt(include_movement=True)
    assert "Movement" in prompt or "movement" in prompt.lower()
    assert "42%" in prompt or "Blocked" in prompt or "blocked" in prompt


def test_user_prompt_movement_stuck_info() -> None:
    prompt = _sample_prompt(include_movement=True)
    assert "2" in prompt  # stuck_episodes = 2
    assert "10" in prompt or "19" in prompt  # worst range


def test_user_prompt_movement_code_flags() -> None:
    prompt = _sample_prompt(include_movement=True)
    assert "is_walkable" in prompt or "walkable" in prompt


def test_user_prompt_no_movement_section_when_omitted() -> None:
    prompt = _sample_prompt(include_movement=False)
    assert "Movement / pathfinding" not in prompt


def test_system_prompt_includes_movement_instruction() -> None:
    assert "movement" in SYSTEM_PROMPT.lower()
