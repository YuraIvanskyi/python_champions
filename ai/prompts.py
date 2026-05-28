"""Prompt templates for Phase 4 AI feedback."""

from __future__ import annotations

from engine.i18n import normalize_lang, translate

# Backward-compatible alias for tests that import SYSTEM_PROMPT
SYSTEM_PROMPT = ""  # filled on first access via system_prompt("en")


def system_prompt(language: str = "en") -> str:
    """System prompt with guard rails (always English; LLM output not locale-forced)."""
    _ = normalize_lang(language)
    return translate("ai.system", lang="en")


def _legacy_system_prompt() -> str:
    global SYSTEM_PROMPT
    if not SYSTEM_PROMPT:
        SYSTEM_PROMPT = system_prompt("en")
    return SYSTEM_PROMPT


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
    language: str = "en",
) -> str:
    """Build the user prompt from session metrics only (no engine internals).

    Prompt text is always English so the model is not instructed to translate its reply.
    *feedback_items* may still reflect the session locale from static/runtime analysis.
    """
    _ = normalize_lang(language)
    lang = "en"
    lines: list[str] = [
        translate("ai.prompt.scenario", lang=lang, name=scenario_name),
        translate(
            "ai.prompt.turns",
            lang=lang,
            turns=turn_count,
            resources=resources_gathered,
            threshold=score_threshold,
        ),
        translate(
            "ai.prompt.scores",
            lang=lang,
            gameplay=gameplay_score,
            quality=code_quality_score,
            final=final_score,
        ),
        "",
    ]

    if action_distribution:
        total_actions = sum(action_distribution.values())
        lines.append(translate("ai.prompt.action_breakdown", lang=lang))
        for action, count in sorted(action_distribution.items(), key=lambda kv: -kv[1]):
            pct = round(100 * count / total_actions) if total_actions else 0
            lines.append(
                translate(
                    "ai.prompt.action_line",
                    lang=lang,
                    action=action,
                    count=count,
                    pct=pct,
                )
            )
        lines.append("")

    if score_trajectory:
        turns_with_score = [(t, s) for t, s in score_trajectory if s > 0]
        if turns_with_score:
            first_score_turn, _ = turns_with_score[0]
            mid = turn_count // 2
            mid_score = next((s for t, s in score_trajectory if t >= mid), 0)
            final_game_score = score_trajectory[-1][1] if score_trajectory else 0
            lines.append(
                translate(
                    "ai.prompt.score_progress",
                    lang=lang,
                    first=first_score_turn,
                    mid=mid,
                    mid_score=mid_score,
                    final_score=final_game_score,
                )
            )
            lines.append("")

    if avg_turn_ms or timeout_count or crash_count or invalid_action_count:
        lines.append(
            translate(
                "ai.prompt.runtime",
                lang=lang,
                avg=avg_turn_ms,
                timeouts=timeout_count,
                crashes=crash_count,
                invalid=invalid_action_count,
            )
        )
        lines.append("")

    _movement = movement or {}
    _static_mv = static_movement or {}
    if _movement.get("analyzed"):
        blocked_pct = int(float(_movement.get("blocked_move_ratio", 0)) * 100)
        wait_pct = int(float(_movement.get("wait_ratio", 0)) * 100)
        stuck = int(_movement.get("stuck_episodes", 0))
        osc = int(_movement.get("oscillation_episodes", 0))
        repeat = int(_movement.get("max_consecutive_same_action", 0))
        stall = int(_movement.get("score_stall_turns", 0))
        unique_pct = int(float(_movement.get("unique_positions_ratio", 0)) * 100)
        worst_range: list[int] = _movement.get("worst_stuck_turn_range") or []

        lines.append(translate("ai.prompt.movement_header", lang=lang))
        lines.append(
            translate(
                "ai.prompt.movement_blocked",
                lang=lang,
                blocked=blocked_pct,
                wait=wait_pct,
            )
        )
        range_suffix = ""
        if len(worst_range) == 2:
            range_suffix = translate(
                "ai.prompt.movement_stuck_range",
                lang=lang,
                start=worst_range[0],
                end=worst_range[1],
            )
        lines.append(
            translate("ai.prompt.movement_stuck", lang=lang, stuck=stuck, range=range_suffix)
        )
        lines.append(translate("ai.prompt.movement_osc", lang=lang, osc=osc))
        lines.append(translate("ai.prompt.movement_repeat", lang=lang, repeat=repeat))
        lines.append(translate("ai.prompt.movement_stall", lang=lang, stall=stall))
        lines.append(translate("ai.prompt.movement_unique", lang=lang, unique=unique_pct))

        code_flags: list[str] = []
        if _static_mv.get("no_walkable_check"):
            code_flags.append(translate("ai.flag.no_walkable", lang=lang))
        if _static_mv.get("constant_action_return"):
            code_flags.append(translate("ai.flag.constant_return", lang=lang))
        if _static_mv.get("no_target_logic"):
            code_flags.append(translate("ai.flag.no_target", lang=lang))
        if _static_mv.get("missing_fallback"):
            code_flags.append(translate("ai.flag.no_fallback", lang=lang))
        if code_flags:
            lines.append(
                translate("ai.prompt.code_flags", lang=lang, flags=", ".join(code_flags))
            )
        lines.append("")

    lines.append(
        translate(
            "ai.prompt.code_structure",
            lang=lang,
            rank=complexity_rank,
            depth=max_nesting_depth,
            lines=function_line_count,
        )
    )
    lines.append("")

    lines.append(translate("ai.prompt.feedback_header", lang=lang))
    if feedback_items:
        for item in feedback_items:
            lines.append(translate("ai.prompt.feedback_item", lang=lang, item=item))
    else:
        lines.append(translate("ai.prompt.no_issues", lang=lang))

    if top_ruff_violations:
        lines.append("")
        lines.append(translate("ai.prompt.ruff_header", lang=lang))
        for rule_id, count in top_ruff_violations:
            lines.append(translate("ai.prompt.ruff_line", lang=lang, rule=rule_id, count=count))

    lines.append("")
    lines.append(translate("ai.prompt.write_instruction", lang=lang))

    return "\n".join(lines)


# Populate legacy module attribute for imports expecting SYSTEM_PROMPT at load time
SYSTEM_PROMPT = system_prompt("en")
