"""Template-based educational feedback from analysis metrics."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any

from engine.i18n import normalize_lang, translate
from engine.i18n.feedback_strings import RUFF_PREFIXES

if TYPE_CHECKING:
    from engine.analysis.movement import MovementConfig


def _fb(lang: str, key: str, **kwargs: Any) -> str:
    return translate(key, lang=normalize_lang(lang), **kwargs)


@dataclass
class FeedbackItem:
    id: str
    category: str  # runtime | logic | style | efficiency | praise
    severity: str  # info | warn | critical
    title: str
    message: str
    lines: list[int] = field(default_factory=list)
    fix_hint: str = ""
    panel: str = "parchment"  # parchment | wood | stone

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _item(
    *,
    category: str,
    severity: str,
    title: str,
    message: str,
    fix_hint: str,
    panel: str,
    lines: list[int] | None = None,
) -> FeedbackItem:
    return FeedbackItem(
        id=uuid.uuid4().hex[:10],
        category=category,
        severity=severity,
        title=title,
        message=message,
        lines=list(lines or []),
        fix_hint=fix_hint,
        panel=panel,
    )


_RUFF_INLINE_THRESHOLD = 10  # show individual cards up to this many issues


def _ruff_title(code: str, lang: str) -> str:
    for prefix in RUFF_PREFIXES:
        if code.startswith(prefix):
            key = f"feedback.ruff.{prefix}.title"
            val = _fb(lang, key)
            if val != key:
                return val
    return _fb(lang, "feedback.ruff.default_title")


def _ruff_fix_hint(code: str, lang: str) -> str:
    for prefix in RUFF_PREFIXES:
        if code.startswith(prefix):
            key = f"feedback.ruff.{prefix}.fix_hint"
            val = _fb(lang, key)
            if val != key:
                return val
    return _fb(lang, "feedback.ruff.default_hint")


def _ruff_lines(static: dict[str, Any]) -> list[int]:
    lines: list[int] = []
    for v in static.get("ruff", []):
        line = v.get("line")
        if isinstance(line, int) and line not in lines:
            lines.append(line)
    return sorted(lines)


def _forbidden_lines(static: dict[str, Any]) -> list[int]:
    lines: list[int] = []
    for entry in static.get("forbidden_constructs", []):
        if not isinstance(entry, dict):
            continue
        line = entry.get("line") or entry.get("lineno")
        if isinstance(line, int) and line not in lines:
            lines.append(line)
    return sorted(lines)


def generate_feedback_items(
    *,
    static: dict[str, Any],
    runtime: dict[str, Any],
    movement: dict[str, Any] | None = None,
    movement_cfg: "MovementConfig | None" = None,
    language: str = "en",
) -> list[FeedbackItem]:
    """Return structured hints ordered by priority (most important first)."""
    from engine.analysis.movement import MovementConfig as _MovementConfig

    lang = normalize_lang(language)
    _mcfg = movement_cfg or _MovementConfig()
    _mv = movement or {}

    items: list[FeedbackItem] = []

    if runtime.get("timeout_count", 0) > 0:
        items.append(
            _item(
                category="runtime",
                severity="critical",
                title=_fb(lang, "feedback.turn_timeout.title"),
                message=_fb(lang, "feedback.turn_timeout.message"),
                fix_hint=_fb(lang, "feedback.turn_timeout.fix_hint"),
                panel="parchment",
            )
        )

    if runtime.get("crash_count", 0) > 0:
        items.append(
            _item(
                category="runtime",
                severity="critical",
                title=_fb(lang, "feedback.crash.title"),
                message=_fb(lang, "feedback.crash.message"),
                fix_hint=_fb(lang, "feedback.crash.fix_hint"),
                panel="parchment",
            )
        )
        items.append(
            _item(
                category="runtime",
                severity="warn",
                title=_fb(lang, "feedback.crash_cap.title"),
                message=_fb(lang, "feedback.crash_cap.message"),
                fix_hint=_fb(lang, "feedback.crash_cap.fix_hint"),
                panel="stone",
            )
        )

    if runtime.get("invalid_action_count", 0) > 0:
        items.append(
            _item(
                category="logic",
                severity="warn",
                title=_fb(lang, "feedback.invalid_actions.title"),
                message=_fb(lang, "feedback.invalid_actions.message"),
                fix_hint=_fb(lang, "feedback.invalid_actions.fix_hint"),
                panel="wood",
            )
        )

    _movement_items(items, _mv, _mcfg, static, lang)

    max_complexity = static.get("max_complexity", 0)
    if max_complexity >= 10:
        items.append(
            _item(
                category="efficiency",
                severity="warn",
                title=_fb(lang, "feedback.high_complexity.title"),
                message=_fb(lang, "feedback.high_complexity.message"),
                fix_hint=_fb(lang, "feedback.high_complexity.fix_hint"),
                panel="wood",
            )
        )
    elif max_complexity >= 7:
        items.append(
            _item(
                category="efficiency",
                severity="info",
                title=_fb(lang, "feedback.growing_complexity.title"),
                message=_fb(lang, "feedback.growing_complexity.message"),
                fix_hint=_fb(lang, "feedback.growing_complexity.fix_hint"),
                panel="wood",
            )
        )

    max_nesting = static.get("max_nesting_depth", 0)
    if max_nesting >= 4:
        items.append(
            _item(
                category="efficiency",
                severity="warn",
                title=_fb(lang, "feedback.deep_nesting.title"),
                message=_fb(lang, "feedback.deep_nesting.message"),
                fix_hint=_fb(lang, "feedback.deep_nesting.fix_hint"),
                panel="wood",
            )
        )

    max_lines = static.get("max_function_lines", 0)
    if max_lines >= 50:
        items.append(
            _item(
                category="efficiency",
                severity="warn",
                title=_fb(lang, "feedback.long_function.title"),
                message=_fb(lang, "feedback.long_function.message"),
                fix_hint=_fb(lang, "feedback.long_function.fix_hint"),
                panel="wood",
            )
        )

    ruff = static.get("ruff", [])
    if ruff:
        if len(ruff) <= _RUFF_INLINE_THRESHOLD:
            # Show one card per issue so students can tackle them one by one
            for violation in ruff:
                code    = str(violation.get("code", ""))
                line    = violation.get("line")
                message = str(violation.get("message", ""))
                items.append(
                    _item(
                        category="style",
                        severity="warn",
                        title=_ruff_title(code, lang),
                        message=message,
                        fix_hint=_ruff_fix_hint(code, lang),
                        panel="stone",
                        lines=[line] if isinstance(line, int) else [],
                    )
                )
        else:
            ruff_lines = _ruff_lines(static)
            items.append(
                _item(
                    category="style",
                    severity="warn",
                    title=_fb(lang, "feedback.style_many.title", count=len(ruff)),
                    message=_fb(lang, "feedback.style_many.message", count=len(ruff)),
                    fix_hint=_fb(lang, "feedback.style_many.fix_hint"),
                    panel="stone",
                    lines=ruff_lines,
                )
            )

    forbidden_lines = _forbidden_lines(static)
    forbidden = static.get("forbidden_constructs", [])
    if forbidden:
        items.append(
            _item(
                category="logic",
                severity="critical",
                title=_fb(lang, "feedback.forbidden.title"),
                message=_fb(lang, "feedback.forbidden.message"),
                fix_hint=_fb(lang, "feedback.forbidden.fix_hint"),
                panel="stone",
                lines=forbidden_lines,
            )
        )

    unused = static.get("unused_names", [])
    if len(unused) >= 2:
        items.append(
            _item(
                category="style",
                severity="info",
                title=_fb(lang, "feedback.unused_vars.title"),
                message=_fb(lang, "feedback.unused_vars.message"),
                fix_hint=_fb(lang, "feedback.unused_vars.fix_hint"),
                panel="parchment",
            )
        )

    for fn in static.get("functions", []):
        mi = fn.get("maintainability_index")
        if mi is not None and mi < 20:
            fn_name = fn.get("name", "?")
            fn_lines = [fn["line"]] if isinstance(fn.get("line"), int) else []
            items.append(
                _item(
                    category="efficiency",
                    severity="warn",
                    title=_fb(lang, "feedback.low_maint.title", name=fn_name),
                    message=_fb(lang, "feedback.low_maint.message", name=fn_name),
                    fix_hint=_fb(lang, "feedback.low_maint.fix_hint"),
                    panel="wood",
                    lines=fn_lines,
                )
            )
            break

    avg_ms = runtime.get("avg_turn_time_ms", 0)
    if avg_ms > 200 and runtime.get("total_turns", 0) > 0:
        items.append(
            _item(
                category="runtime",
                severity="info",
                title=_fb(lang, "feedback.slow_turns.title"),
                message=_fb(lang, "feedback.slow_turns.message"),
                fix_hint=_fb(lang, "feedback.slow_turns.fix_hint"),
                panel="parchment",
            )
        )

    if static.get("ast_error"):
        items.append(
            _item(
                category="logic",
                severity="critical",
                title=_fb(lang, "feedback.syntax.title"),
                message=_fb(lang, "feedback.syntax.message"),
                fix_hint=_fb(lang, "feedback.syntax.fix_hint"),
                panel="stone",
            )
        )

    if not items:
        items.append(
            _item(
                category="praise",
                severity="info",
                title=_fb(lang, "feedback.praise.title"),
                message=_fb(lang, "feedback.praise.message"),
                fix_hint=_fb(lang, "feedback.praise.fix_hint"),
                panel="parchment",
            )
        )

    return items


def _movement_items(
    items: list[FeedbackItem],
    mv: dict[str, Any],
    cfg: "MovementConfig",
    static: dict[str, Any],
    lang: str,
) -> None:
    """Append movement-quality feedback cards to *items* (mutates in place)."""
    if not mv.get("analyzed", False):
        _movement_static_items(items, static, lang)
        return

    static_mv: dict[str, Any] = static.get("movement", {})
    make_turn_line: int | None = static_mv.get("make_turn_line")
    hint_lines = [make_turn_line] if isinstance(make_turn_line, int) else []

    # Stuck between obstacles
    stuck = int(mv.get("stuck_episodes", 0))
    if stuck >= 1:
        stuck_range: list[int] = mv.get("worst_stuck_turn_range") or []
        range_str = ""
        if len(stuck_range) == 2:
            range_str = _fb(
                lang, "feedback.stuck.range", start=stuck_range[0], end=stuck_range[1],
            )
        plural = _fb(lang, "feedback.plural.s") if stuck > 1 else _fb(lang, "feedback.plural.empty")
        items.append(
            _item(
                category="logic",
                severity="warn",
                title=_fb(lang, "feedback.stuck.title"),
                message=_fb(
                    lang, "feedback.stuck.message",
                    count=stuck, plural=plural, range=range_str,
                ),
                fix_hint=_fb(lang, "feedback.stuck.fix_hint"),
                panel="wood",
                lines=hint_lines,
            )
        )

    osc = int(mv.get("oscillation_episodes", 0))
    if osc >= 1:
        plural = _fb(lang, "feedback.plural.s") if osc > 1 else _fb(lang, "feedback.plural.empty")
        items.append(
            _item(
                category="logic",
                severity="warn",
                title=_fb(lang, "feedback.oscillation.title"),
                message=_fb(lang, "feedback.oscillation.message", count=osc, plural=plural),
                fix_hint=_fb(lang, "feedback.oscillation.fix_hint"),
                panel="wood",
                lines=hint_lines,
            )
        )

    max_run = int(mv.get("max_consecutive_same_action", 0))
    if max_run >= cfg.consecutive_action_warn:
        items.append(
            _item(
                category="logic",
                severity="warn",
                title=_fb(lang, "feedback.repeat_action.title"),
                message=_fb(lang, "feedback.repeat_action.message", count=max_run),
                fix_hint=_fb(lang, "feedback.repeat_action.fix_hint"),
                panel="wood",
                lines=hint_lines,
            )
        )

    blocked_ratio = float(mv.get("blocked_move_ratio", 0.0))
    no_walkable = static_mv.get("no_walkable_check", False)
    if blocked_ratio >= cfg.blocked_ratio_warn:
        pct = int(blocked_ratio * 100)
        extra = _fb(lang, "feedback.blocked_moves.extra_no_walkable") if no_walkable else ""
        items.append(
            _item(
                category="logic",
                severity="warn",
                title=_fb(lang, "feedback.blocked_moves.title"),
                message=_fb(lang, "feedback.blocked_moves.message", pct=pct, extra=extra),
                fix_hint=_fb(lang, "feedback.blocked_moves.fix_hint"),
                panel="wood",
                lines=hint_lines if no_walkable else [],
            )
        )
    elif no_walkable and blocked_ratio > 0:
        items.append(
            _item(
                category="logic",
                severity="info",
                title=_fb(lang, "feedback.no_walkable.title"),
                message=_fb(lang, "feedback.no_walkable.message"),
                fix_hint=_fb(lang, "feedback.no_walkable.fix_hint"),
                panel="parchment",
                lines=hint_lines,
            )
        )

    stall = int(mv.get("score_stall_turns", 0))
    if stall >= cfg.score_stall_warn:
        items.append(
            _item(
                category="logic",
                severity="info",
                title=_fb(lang, "feedback.score_stall.title"),
                message=_fb(lang, "feedback.score_stall.message", stall=stall),
                fix_hint=_fb(lang, "feedback.score_stall.fix_hint"),
                panel="parchment",
                lines=hint_lines,
            )
        )

    if static_mv.get("constant_action_return", False):
        items.append(
            _item(
                category="logic",
                severity="warn",
                title=_fb(lang, "feedback.no_branch.title"),
                message=_fb(lang, "feedback.no_branch.message"),
                fix_hint=_fb(lang, "feedback.no_branch.fix_hint"),
                panel="stone",
                lines=hint_lines,
            )
        )

    if static_mv.get("no_target_logic", False) and not static_mv.get("constant_action_return", False):
        items.append(
            _item(
                category="logic",
                severity="info",
                title=_fb(lang, "feedback.no_target.title"),
                message=_fb(lang, "feedback.no_target.message"),
                fix_hint=_fb(lang, "feedback.no_target.fix_hint"),
                panel="parchment",
                lines=hint_lines,
            )
        )

    if static_mv.get("missing_fallback", False) and not stuck and not osc:
        items.append(
            _item(
                category="logic",
                severity="info",
                title=_fb(lang, "feedback.no_fallback.title"),
                message=_fb(lang, "feedback.no_fallback.message"),
                fix_hint=_fb(lang, "feedback.no_fallback.fix_hint"),
                panel="parchment",
                lines=hint_lines,
            )
        )


def _movement_static_items(items: list[FeedbackItem], static: dict[str, Any], lang: str) -> None:
    """Emit static-only movement cards when no replay data is available."""
    static_mv: dict[str, Any] = static.get("movement", {})
    make_turn_line: int | None = static_mv.get("make_turn_line")
    hint_lines = [make_turn_line] if isinstance(make_turn_line, int) else []

    if static_mv.get("constant_action_return", False):
        items.append(
            _item(
                category="logic",
                severity="warn",
                title=_fb(lang, "feedback.no_branch.title"),
                message=_fb(lang, "feedback.no_branch.message"),
                fix_hint=_fb(lang, "feedback.no_branch.fix_hint_static"),
                panel="stone",
                lines=hint_lines,
            )
        )

    if static_mv.get("no_walkable_check", False):
        items.append(
            _item(
                category="logic",
                severity="info",
                title=_fb(lang, "feedback.no_walkable.title"),
                message=_fb(lang, "feedback.no_walkable.message_static"),
                fix_hint=_fb(lang, "feedback.no_walkable.fix_hint"),
                panel="parchment",
                lines=hint_lines,
            )
        )

    if static_mv.get("no_target_logic", False) and not static_mv.get("constant_action_return", False):
        items.append(
            _item(
                category="logic",
                severity="info",
                title=_fb(lang, "feedback.no_target.title"),
                message=_fb(lang, "feedback.no_target.message_static"),
                fix_hint=_fb(lang, "feedback.no_target.fix_hint"),
                panel="parchment",
                lines=hint_lines,
            )
        )


def generate_feedback(
    *,
    static: dict[str, Any],
    runtime: dict[str, Any],
    movement: dict[str, Any] | None = None,
    movement_cfg: "MovementConfig | None" = None,
    language: str = "en",
) -> list[str]:
    """Return plain-language hints ordered by priority (CLI / legacy JSON)."""
    return [
        item.message
        for item in generate_feedback_items(
            static=static,
            runtime=runtime,
            movement=movement,
            movement_cfg=movement_cfg,
            language=language,
        )
    ]
