"""Normalize static metrics to a 0–100 code quality score.

Formula (documented for teachers):
  Start at 100, subtract penalties (clamped 0–100):
  - Ruff violations: 5 points each, max 40 total
  - max cyclomatic complexity: 8 if >=7, +7 more if >=10
  - max nesting depth: 8 if >=3, +7 more if >=4
  - max function lines: 10 if >=40, +5 more if >=60
  - forbidden constructs: 20 each, max 40
  - unused names: 3 each, max 15
  - lowest MI < 20: 12
  - syntax error (ast_error): score 0
"""

from __future__ import annotations

from typing import Any


def compute_code_quality(static: dict[str, Any]) -> int:
    if static.get("ast_error"):
        return 0

    score = 100

    ruff_count = len(static.get("ruff", []))
    score -= min(40, ruff_count * 5)

    complexity = int(static.get("max_complexity", 0))
    if complexity >= 10:
        score -= 15
    elif complexity >= 7:
        score -= 8

    nesting = int(static.get("max_nesting_depth", 0))
    if nesting >= 4:
        score -= 15
    elif nesting >= 3:
        score -= 8

    fn_lines = int(static.get("max_function_lines", 0))
    if fn_lines >= 60:
        score -= 15
    elif fn_lines >= 40:
        score -= 10

    forbidden = static.get("forbidden_constructs", [])
    score -= min(40, len(forbidden) * 20)

    unused = static.get("unused_names", [])
    score -= min(15, len(unused) * 3)

    for fn in static.get("functions", []):
        mi = fn.get("maintainability_index")
        if mi is not None and mi < 20:
            score -= 12
            break

    return max(0, min(100, score))
