"""Template-based educational feedback from analysis metrics."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


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


_RUFF_INLINE_THRESHOLD = 7   # show individual cards up to this many issues

# Maps ruff code *prefixes* → short kid-friendly card title
_RUFF_TITLE_MAP: list[tuple[str, str]] = [
    ("E1", "Indentation issue"),
    ("E2", "Whitespace issue"),
    ("E3", "Blank line issue"),
    ("E4", "Import order"),
    ("E5", "Line too long"),
    ("E7", "Statement issue"),
    ("E9", "Runtime error"),
    ("W2", "Trailing whitespace"),
    ("W3", "Blank line warning"),
    ("W5", "Line-break warning"),
    ("W6", "Deprecated syntax"),
    ("F4", "Unused import"),
    ("F8", "Unused name"),
    ("F9", "Undefined name"),
    ("N",  "Naming convention"),
    ("B",  "Possible bug"),
    ("C9", "High complexity"),
    ("E",  "Style issue"),
    ("W",  "Style warning"),
    ("F",  "Code problem"),
]


def _ruff_title(code: str) -> str:
    for prefix, title in _RUFF_TITLE_MAP:
        if code.startswith(prefix):
            return title
    return "Style check"


def _ruff_fix_hint(code: str) -> str:
    if code.startswith("F4") or code.startswith("E4"):
        return "Remove or sort the import at the top of the file."
    if code.startswith("F8"):
        return "Delete the name if you don't use it, or use it in your logic."
    if code.startswith("F9"):
        return "Check the spelling — the name must be defined before you use it."
    if code.startswith("E1"):
        return "Fix the indentation — use 4 spaces per level."
    if code.startswith("E2") or code.startswith("W2"):
        return "Remove extra spaces or add a missing one around the operator."
    if code.startswith("E3") or code.startswith("W3"):
        return "Add or remove the blank line as the message describes."
    if code.startswith("E5"):
        return "Break the long line into two shorter ones."
    if code.startswith("E7"):
        return "Rewrite the statement as shown in the message."
    if code.startswith("B"):
        return "Read the message carefully — this pattern can hide a bug."
    if code.startswith("N"):
        return "Rename the variable/function to follow the naming rule shown."
    return "Read the message and fix the highlighted line."


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
) -> list[FeedbackItem]:
    """Return structured hints ordered by priority (most important first)."""
    items: list[FeedbackItem] = []

    if runtime.get("timeout_count", 0) > 0:
        items.append(
            _item(
                category="runtime",
                severity="critical",
                title="Turn timeout",
                message=(
                    "Your bot timed out on one or more turns. "
                    "Try simpler logic or fewer loops so each turn finishes faster."
                ),
                fix_hint="Shorten loops and avoid heavy work inside make_turn.",
                panel="parchment",
            )
        )

    if runtime.get("crash_count", 0) > 0:
        items.append(
            _item(
                category="runtime",
                severity="critical",
                title="Bot crashed",
                message=(
                    "Your bot crashed during the game. "
                    "Check for typos, missing keys in game_state, or bad return values."
                ),
                fix_hint="Run the bot locally and fix the first error Python reports.",
                panel="parchment",
            )
        )

    if runtime.get("invalid_action_count", 0) > 0:
        items.append(
            _item(
                category="logic",
                severity="warn",
                title="Invalid actions",
                message=(
                    "Some turns used invalid actions (for example GATHER when not on a resource). "
                    "Read the allowed actions in the bot template comments."
                ),
                fix_hint="Use GameView helpers (on_resource, is_walkable) before returning an action.",
                panel="wood",
            )
        )

    max_complexity = static.get("max_complexity", 0)
    if max_complexity >= 10:
        items.append(
            _item(
                category="efficiency",
                severity="warn",
                title="High complexity",
                message=(
                    "Your code has high cyclomatic complexity. "
                    "Try splitting logic into smaller functions with clear names."
                ),
                fix_hint="Extract one helper per decision (movement, gathering, targeting).",
                panel="wood",
            )
        )
    elif max_complexity >= 7:
        items.append(
            _item(
                category="efficiency",
                severity="info",
                title="Growing complexity",
                message=(
                    "Some functions are getting complex. "
                    "Extract helper functions for repeated conditions."
                ),
                fix_hint="Name helpers after what they check, e.g. should_gather(state).",
                panel="wood",
            )
        )

    max_nesting = static.get("max_nesting_depth", 0)
    if max_nesting >= 4:
        items.append(
            _item(
                category="efficiency",
                severity="warn",
                title="Deep nesting",
                message=(
                    "Deeply nested if/for blocks make code hard to follow. "
                    "Use early returns or helper functions to flatten structure."
                ),
                fix_hint="Return early when a condition fails instead of wrapping more code.",
                panel="wood",
            )
        )

    max_lines = static.get("max_function_lines", 0)
    if max_lines >= 50:
        items.append(
            _item(
                category="efficiency",
                severity="warn",
                title="Long function",
                message=(
                    "One of your functions is very long. "
                    "Break it into smaller steps — each function should do one clear job."
                ),
                fix_hint="Split make_turn into decide_action + small helpers.",
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
                        title=_ruff_title(code),
                        message=message,
                        fix_hint=_ruff_fix_hint(code),
                        panel="stone",
                        lines=[line] if isinstance(line, int) else [],
                    )
                )
        else:
            # Too many to list individually — show a summary card
            ruff_lines = _ruff_lines(static)
            items.append(
                _item(
                    category="style",
                    severity="warn",
                    title=f"Style check  ({len(ruff)} issues)",
                    message=(
                        f"Found {len(ruff)} style issues in your code. "
                        "Fix the highlighted lines — clean code is easier to read and debug."
                    ),
                    fix_hint="Work through the highlighted lines one by one.",
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
                title="Forbidden imports",
                message=(
                    "Your bot uses imports or calls that are not allowed in the sandbox "
                    "(for example os or subprocess). Stick to the student API only."
                ),
                fix_hint="Remove blocked imports; use only GameView and allowed actions.",
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
                title="Unused variables",
                message=(
                    "You have variables that are assigned but never used. "
                    "Remove dead code or use those variables in your logic."
                ),
                fix_hint="Delete assignments you do not need, or wire them into decisions.",
                panel="parchment",
            )
        )

    for fn in static.get("functions", []):
        mi = fn.get("maintainability_index")
        if mi is not None and mi < 20:
            fn_lines = [fn["line"]] if isinstance(fn.get("line"), int) else []
            items.append(
                _item(
                    category="efficiency",
                    severity="warn",
                    title=f"Low maintainability: {fn.get('name', '?')}",
                    message=(
                        f"Function '{fn.get('name', '?')}' has low maintainability. "
                        "Simplify conditions and shorten the function."
                    ),
                    fix_hint="Break this function into two smaller ones.",
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
                title="Slow turns",
                message=(
                    "Turns are taking a long time on average. "
                    "Avoid scanning the whole map every turn if you can cache simpler rules."
                ),
                fix_hint="Cache last direction or nearest resource instead of full-map scans.",
                panel="parchment",
            )
        )

    if static.get("ast_error"):
        items.append(
            _item(
                category="logic",
                severity="critical",
                title="Syntax error",
                message=(
                    "Your bot file has a Python syntax error. "
                    "The game cannot analyze code quality until the file parses correctly."
                ),
                fix_hint="Fix the syntax error shown when you run the file in Python.",
                panel="stone",
            )
        )

    if not items:
        items.append(
            _item(
                category="praise",
                severity="info",
                title="Looking good",
                message=(
                    "Nice work — no major issues flagged. "
                    "Keep refactoring as you add features."
                ),
                fix_hint="Try a harder opponent or add smarter gathering logic.",
                panel="parchment",
            )
        )

    return items


def generate_feedback(
    *,
    static: dict[str, Any],
    runtime: dict[str, Any],
) -> list[str]:
    """Return plain-language hints ordered by priority (CLI / legacy JSON)."""
    return [item.message for item in generate_feedback_items(static=static, runtime=runtime)]
