"""Prompt templates for Phase 4 AI feedback.

Guard rails (PLAN.md §7, §23.3):
- System prompt forbids full solutions and code rewrites.
- User prompt contains only metrics / scores / feedback templates — never raw
  engine internals, class internals, or the full student source.
"""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are an educational code analysis assistant for a student programming game.

Rules you must follow:
1. Do NOT generate full solutions or rewrite the student's code.
2. Do NOT show corrected code snippets longer than one line.
3. Keep your student summary to at most 5 sentences.
4. Keep your teacher notes to at most 3 bullet points.
5. Be encouraging and constructive; avoid harsh language.
6. Base your analysis only on the metrics and feedback provided — do not invent issues.
"""


def build_user_prompt(
    *,
    scenario_name: str,
    turn_count: int,
    gameplay_score: float,
    code_quality_score: float,
    final_score: float,
    feedback_items: list[str],
    top_ruff_violations: list[tuple[str, int]],
) -> str:
    """Build the user prompt from session metrics only (no engine internals)."""
    lines: list[str] = [
        f"Scenario: {scenario_name}",
        f"Turns played: {turn_count}",
        f"Scores — gameplay: {gameplay_score}, code quality: {code_quality_score}, "
        f"final (weighted): {final_score}",
        "",
        "Feedback from static / runtime analysis:",
    ]

    if feedback_items:
        for item in feedback_items:
            lines.append(f"  - {item}")
    else:
        lines.append("  (no issues detected)")

    if top_ruff_violations:
        lines.append("")
        lines.append("Top style / lint issues (Ruff rule IDs → occurrence count):")
        for rule_id, count in top_ruff_violations:
            lines.append(f"  - {rule_id}: {count} occurrence(s)")

    lines.append("")
    lines.append(
        "Please write:\n"
        "1. **Student summary** — short, friendly explanation of how the bot performed "
        "and what to improve.\n"
        "2. **Teacher notes** — 3 bullet points highlighting the most important code quality "
        "observations for the teacher's review."
    )

    return "\n".join(lines)
