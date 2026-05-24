"""Phase 4: Prompt content guard-rails."""

from __future__ import annotations

from ai.prompts import SYSTEM_PROMPT, build_user_prompt


def _sample_prompt() -> str:
    return build_user_prompt(
        scenario_name="resource_wars",
        turn_count=50,
        gameplay_score=72.0,
        code_quality_score=65.0,
        final_score=70.1,
        feedback_items=["Avoid bare except clauses", "Add docstring to make_turn"],
        top_ruff_violations=[("E501", 3), ("F401", 2)],
    )


def test_system_prompt_forbids_full_solutions() -> None:
    lower = SYSTEM_PROMPT.lower()
    assert "do not generate full solutions" in lower or "not generate full solutions" in lower


def test_system_prompt_forbids_rewriting_code() -> None:
    lower = SYSTEM_PROMPT.lower()
    assert "rewrite" in lower


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
