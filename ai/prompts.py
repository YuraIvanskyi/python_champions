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
2. You MAY include a tiny code example (1–2 lines maximum) inside a fenced code block \
(``` … ```) when it concretely illustrates a specific improvement — for example showing \
the corrected form of a single bad expression. Keep the block self-contained.
3. Keep your student summary to at most 5 sentences.
4. Keep your teacher notes to at most 3 bullet points.
5. Be encouraging and constructive; avoid harsh language.
6. Base your analysis only on the metrics and feedback provided — including movement \
patterns — do not invent issues.
7. When describing the bot's strategy, refer to the action distribution and movement data provided.
"""


def build_user_prompt(
    *,
    scenario_name: str,
    turn_count: int,
    gameplay_score: float,
    code_quality_score: float,
    final_score: float,
    resources_gathered: int,
    score_threshold: int,
    feedback_items: list[str],
    top_ruff_violations: list[tuple[str, int]],
    action_distribution: dict[str, int],
    score_trajectory: list[tuple[int, int]],
    avg_turn_ms: float,
    timeout_count: int,
    crash_count: int,
    invalid_action_count: int,
    complexity_rank: str,
    max_nesting_depth: int,
    function_line_count: int,
    movement: dict | None = None,
    static_movement: dict | None = None,
) -> str:
    """Build the user prompt from session metrics only (no engine internals)."""
    lines: list[str] = [
        f"Scenario: {scenario_name}",
        f"Turns played: {turn_count}  |  Resources gathered: {resources_gathered}"
        f"  |  Score threshold (win): {score_threshold}",
        f"Scores — gameplay: {gameplay_score}/100, code quality: {code_quality_score}/100,"
        f" final (weighted 70/30): {final_score}",
        "",
    ]

    # ── Game flow & algorithm ─────────────────────────────────────────────────
    if action_distribution:
        total_actions = sum(action_distribution.values())
        lines.append("Bot action breakdown (what it did each turn):")
        for action, count in sorted(action_distribution.items(), key=lambda kv: -kv[1]):
            pct = round(100 * count / total_actions) if total_actions else 0
            lines.append(f"  - {action}: {count} turns ({pct}%)")
        lines.append("")

    if score_trajectory:
        # Summarise when scoring happened: first gather turn, score by mid-game
        turns_with_score = [(t, s) for t, s in score_trajectory if s > 0]
        if turns_with_score:
            first_score_turn, _ = turns_with_score[0]
            mid = turn_count // 2
            mid_score = next((s for t, s in score_trajectory if t >= mid), 0)
            final_game_score = score_trajectory[-1][1] if score_trajectory else 0
            lines.append(
                f"Score progression: first resource gathered on turn {first_score_turn}; "
                f"score at mid-game (turn {mid}): {mid_score}; "
                f"final game score: {final_game_score}"
            )
            lines.append("")

    if avg_turn_ms or timeout_count or crash_count or invalid_action_count:
        lines.append(
            f"Runtime: avg turn {avg_turn_ms:.1f} ms  |  timeouts: {timeout_count}"
            f"  |  crashes: {crash_count}  |  invalid actions: {invalid_action_count}"
        )
        lines.append("")

    # ── Movement / pathfinding analysis ──────────────────────────────────────
    _movement = movement or {}
    _static_mv = static_movement or {}
    if _movement.get("analyzed"):
        blocked_pct = int(float(_movement.get("blocked_move_ratio", 0)) * 100)
        wait_pct    = int(float(_movement.get("wait_ratio", 0)) * 100)
        stuck       = int(_movement.get("stuck_episodes", 0))
        osc         = int(_movement.get("oscillation_episodes", 0))
        repeat      = int(_movement.get("max_consecutive_same_action", 0))
        stall       = int(_movement.get("score_stall_turns", 0))
        unique_pct  = int(float(_movement.get("unique_positions_ratio", 0)) * 100)
        worst_range: list[int] = _movement.get("worst_stuck_turn_range") or []

        lines.append("Movement / pathfinding analysis:")
        lines.append(f"  - Blocked move ratio: {blocked_pct}%  |  Wait ratio: {wait_pct}%")
        lines.append(f"  - Stuck episodes: {stuck}" + (
            f" (worst: turns {worst_range[0]}–{worst_range[1]})" if len(worst_range) == 2 else ""
        ))
        lines.append(f"  - Oscillation (ping-pong) episodes: {osc}")
        lines.append(f"  - Max consecutive same action: {repeat} turns")
        lines.append(f"  - Score stall while moving: {stall} turns")
        lines.append(f"  - Unique positions visited: {unique_pct}% of turns")

        code_flags: list[str] = []
        if _static_mv.get("no_walkable_check"):
            code_flags.append("no is_walkable() call")
        if _static_mv.get("constant_action_return"):
            code_flags.append("constant return (no branching)")
        if _static_mv.get("no_target_logic"):
            code_flags.append("no goal-seeking helpers used")
        if _static_mv.get("missing_fallback"):
            code_flags.append("no WAIT/fallback in movement helper")
        if code_flags:
            lines.append(f"  - Code pattern flags: {', '.join(code_flags)}")
        lines.append("")

    # ── Code structure ────────────────────────────────────────────────────────
    lines.append(
        f"Code structure: make_turn complexity rank {complexity_rank}"
        f"  |  max nesting depth: {max_nesting_depth}"
        f"  |  function length: {function_line_count} lines"
    )
    lines.append("")

    # ── Static / runtime feedback ─────────────────────────────────────────────
    lines.append("Feedback from static / runtime analysis:")
    if feedback_items:
        for item in feedback_items:
            lines.append(f"  - {item}")
    else:
        lines.append("  (no issues detected)")

    if top_ruff_violations:
        lines.append("")
        lines.append("Top style / lint issues (Ruff rule ID → occurrences):")
        for rule_id, count in top_ruff_violations:
            lines.append(f"  - {rule_id}: {count}")

    lines.append("")
    lines.append(
        "Please write:\n"
        "### Student Summary\n"
        "A short, friendly explanation referencing what actions the bot took most often "
        "and how that affected its score. Mention one concrete thing to improve.\n\n"
        "### Teacher Notes\n"
        "3 bullet points for the teacher covering: algorithm strategy, code quality "
        "observations, and one actionable next challenge for the student."
    )

    return "\n".join(lines)
