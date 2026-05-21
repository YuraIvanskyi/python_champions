"""Template-based educational feedback from analysis metrics."""

from __future__ import annotations

from typing import Any


def generate_feedback(
    *,
    static: dict[str, Any],
    runtime: dict[str, Any],
) -> list[str]:
    """Return plain-language hints ordered by priority (most important first)."""
    messages: list[str] = []

    if runtime.get("timeout_count", 0) > 0:
        messages.append(
            "Your bot timed out on one or more turns. "
            "Try simpler logic or fewer loops so each turn finishes faster."
        )

    if runtime.get("crash_count", 0) > 0:
        messages.append(
            "Your bot crashed during the game. "
            "Check for typos, missing keys in game_state, or bad return values."
        )

    if runtime.get("invalid_action_count", 0) > 0:
        messages.append(
            "Some turns used invalid actions (for example GATHER when not on a resource). "
            "Read the allowed actions in the bot template comments."
        )

    max_complexity = static.get("max_complexity", 0)
    if max_complexity >= 10:
        messages.append(
            "Your code has high cyclomatic complexity. "
            "Try splitting logic into smaller functions with clear names."
        )
    elif max_complexity >= 7:
        messages.append(
            "Some functions are getting complex. "
            "Extract helper functions for repeated conditions."
        )

    max_nesting = static.get("max_nesting_depth", 0)
    if max_nesting >= 4:
        messages.append(
            "Deeply nested if/for blocks make code hard to follow. "
            "Use early returns or helper functions to flatten structure."
        )

    max_lines = static.get("max_function_lines", 0)
    if max_lines >= 50:
        messages.append(
            "One of your functions is very long. "
            "Break it into smaller steps — each function should do one clear job."
        )

    ruff = static.get("ruff", [])
    if ruff:
        messages.append(
            f"Ruff found {len(ruff)} style or error issue(s). "
            "Fix the highlighted lines — clean code is easier to debug."
        )

    forbidden = static.get("forbidden_constructs", [])
    if forbidden:
        messages.append(
            "Your bot uses imports or calls that are not allowed in the sandbox "
            "(for example os or subprocess). Stick to the student API only."
        )

    unused = static.get("unused_names", [])
    if len(unused) >= 2:
        messages.append(
            "You have variables that are assigned but never used. "
            "Remove dead code or use those variables in your logic."
        )

    for fn in static.get("functions", []):
        mi = fn.get("maintainability_index")
        if mi is not None and mi < 20:
            messages.append(
                f"Function '{fn.get('name', '?')}' has low maintainability. "
                "Simplify conditions and shorten the function."
            )
            break

    avg_ms = runtime.get("avg_turn_time_ms", 0)
    if avg_ms > 200 and runtime.get("total_turns", 0) > 0:
        messages.append(
            "Turns are taking a long time on average. "
            "Avoid scanning the whole map every turn if you can cache simpler rules."
        )

    if static.get("ast_error"):
        messages.append(
            "Your bot file has a Python syntax error. "
            "The game cannot analyze code quality until the file parses correctly."
        )

    if not messages:
        messages.append(
            "Nice work — no major issues flagged. "
            "Keep refactoring as you add features."
        )

    return messages
