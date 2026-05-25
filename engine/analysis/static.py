"""Static analysis: Ruff, Radon, and AST metrics for student bot files."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from radon.complexity import cc_rank, cc_visit
from radon.metrics import mi_rank, mi_visit


@dataclass
class RuffViolation:
    code: str
    line: int
    message: str


@dataclass
class FunctionMetrics:
    name: str
    lineno: int
    complexity: int
    complexity_rank: str
    maintainability_index: float | None
    maintainability_rank: str | None
    line_count: int


@dataclass
class StaticMetrics:
    ruff_violations: list[RuffViolation] = field(default_factory=list)
    functions: list[FunctionMetrics] = field(default_factory=list)
    max_complexity: int = 0
    max_nesting_depth: int = 0
    max_function_lines: int = 0
    unused_names: list[str] = field(default_factory=list)
    forbidden_constructs: list[dict[str, Any]] = field(default_factory=list)
    ast_error: str | None = None


def run_ruff(bot_path: Path, *, select: list[str]) -> list[RuffViolation]:
    """Run Ruff on a single file; return parsed violations.

    Uses ``--no-cache`` so stale cache entries never hide real violations, and
    logs any Ruff errors to stderr so silent failures become visible.
    """
    if not select:
        return []
    select_arg = ",".join(select)
    cmd = [
        sys.executable,
        "-m",
        "ruff",
        "check",
        str(bot_path),
        "--select",
        select_arg,
        "--output-format",
        "json",
        "--no-fix",
        "--no-cache",
    ]
    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    # returncode 0 = clean, 1 = violations found, 2+ = Ruff error
    if completed.returncode >= 2 or (not completed.stdout.strip() and completed.stderr.strip()):
        import sys as _sys
        print(
            f"[analysis] ruff error (rc={completed.returncode}): {completed.stderr.strip()[:200]}",
            file=_sys.stderr,
        )
        return []
    if not completed.stdout.strip():
        return []
    try:
        raw = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        import sys as _sys
        print(f"[analysis] ruff JSON parse error: {exc}", file=_sys.stderr)
        return []
    violations: list[RuffViolation] = []
    for item in raw:
        loc = item.get("location", {})
        violations.append(
            RuffViolation(
                code=str(item.get("code", "")),
                line=int(loc.get("row", 0)),
                message=str(item.get("message", "")),
            )
        )
    return violations


def run_radon_and_ast(
    bot_path: Path,
    *,
    forbidden_names: list[str] | None = None,
) -> tuple[list[FunctionMetrics], dict[str, Any]]:
    """Radon complexity/MI plus AST structural metrics."""
    source = bot_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(bot_path))
    blocks = cc_visit(tree)
    mi_result = mi_visit(source, True)
    mi_by_name: dict[str, float] = {}
    mi_rank_by_name: dict[str, str] = {}
    if isinstance(mi_result, (int, float)):
        module_mi = float(mi_result)
        mi_by_name["<module>"] = module_mi
        mi_rank_by_name["<module>"] = mi_rank(module_mi)
    else:
        for block in mi_result:
            mi_by_name[block.name] = block.mi
            mi_rank_by_name[block.name] = mi_rank(block.mi)

    functions: list[FunctionMetrics] = []
    for block in blocks:
        end_line = getattr(block, "endline", block.lineno)
        functions.append(
            FunctionMetrics(
                name=block.name,
                lineno=block.lineno,
                complexity=block.complexity,
                complexity_rank=cc_rank(block.complexity),
                maintainability_index=mi_by_name.get(block.name),
                maintainability_rank=mi_rank_by_name.get(block.name),
                line_count=max(1, end_line - block.lineno + 1),
            )
        )

    ast_extra = _analyze_ast(tree, source, forbidden_names=forbidden_names or [])
    return functions, ast_extra


class _AstAnalyzer(ast.NodeVisitor):
    def __init__(self, forbidden_names: list[str]) -> None:
        self.max_nesting = 0
        self._depth = 0
        self.unused_names: list[str] = []
        self.forbidden_constructs: list[dict[str, Any]] = []
        self._assigned: set[str] = set()
        self._used: set[str] = set()
        self._forbidden = set(forbidden_names)

    def visit(self, node: ast.AST) -> None:
        if isinstance(
            node,
            (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.Match),
        ):
            self._depth += 1
            self.max_nesting = max(self.max_nesting, self._depth)
            super().visit(node)
            self._depth -= 1
            return
        super().visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store):
            self._assigned.add(node.id)
        elif isinstance(node.ctx, ast.Load):
            self._used.add(node.id)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            mod = alias.name.split(".")[0]
            if mod in self._forbidden:
                self.forbidden_constructs.append(
                    {"kind": "import", "name": mod, "line": node.lineno}
                )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            mod = node.module.split(".")[0]
            if mod in self._forbidden:
                self.forbidden_constructs.append(
                    {"kind": "import_from", "name": mod, "line": node.lineno}
                )

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
            self.forbidden_constructs.append(
                {"kind": "call", "name": node.func.id, "line": node.lineno}
            )
        self.generic_visit(node)

    def finalize_unused(self) -> None:
        builtins_ignore = {
            "True",
            "False",
            "None",
            "make_turn",
            "StudentBot",
        }
        for name in sorted(self._assigned - self._used):
            if name.startswith("_") or name in builtins_ignore:
                continue
            self.unused_names.append(name)


def _analyze_ast(
    tree: ast.AST,
    source: str,
    *,
    forbidden_names: list[str],
) -> dict[str, Any]:
    analyzer = _AstAnalyzer(forbidden_names)
    analyzer.visit(tree)
    analyzer.finalize_unused()
    max_fn_lines = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, "end_lineno", node.lineno)
            max_fn_lines = max(max_fn_lines, end - node.lineno + 1)
    return {
        "max_nesting_depth": analyzer.max_nesting,
        "max_function_lines": max_fn_lines,
        "unused_names": analyzer.unused_names,
        "forbidden_constructs": analyzer.forbidden_constructs,
    }


def analyze_static(
    bot_path: Path,
    *,
    ruff_select: list[str],
    forbidden_names: list[str] | None = None,
    enabled: bool = True,
) -> StaticMetrics:
    """Collect static metrics; returns empty shell when disabled."""
    if not enabled:
        return StaticMetrics()

    metrics = StaticMetrics()
    metrics.ruff_violations = run_ruff(bot_path, select=ruff_select)
    try:
        functions, ast_extra = run_radon_and_ast(
            bot_path,
            forbidden_names=forbidden_names,
        )
    except SyntaxError as exc:
        metrics.ast_error = str(exc)
        return metrics

    metrics.functions = functions
    if functions:
        metrics.max_complexity = max(f.complexity for f in functions)
        metrics.max_function_lines = max(f.line_count for f in functions)
    metrics.max_nesting_depth = int(ast_extra["max_nesting_depth"])
    metrics.max_function_lines = max(
        metrics.max_function_lines,
        int(ast_extra["max_function_lines"]),
    )
    metrics.unused_names = list(ast_extra["unused_names"])
    metrics.forbidden_constructs = list(ast_extra["forbidden_constructs"])
    return metrics


def static_to_dict(metrics: StaticMetrics) -> dict[str, Any]:
    return {
        "ruff": [
            {"code": v.code, "line": v.line, "message": v.message}
            for v in metrics.ruff_violations
        ],
        "functions": [
            {
                "name": f.name,
                "line": f.lineno,
                "complexity": f.complexity,
                "complexity_rank": f.complexity_rank,
                "maintainability_index": f.maintainability_index,
                "maintainability_rank": f.maintainability_rank,
                "line_count": f.line_count,
            }
            for f in metrics.functions
        ],
        "max_complexity": metrics.max_complexity,
        "max_nesting_depth": metrics.max_nesting_depth,
        "max_function_lines": metrics.max_function_lines,
        "unused_names": metrics.unused_names,
        "forbidden_constructs": metrics.forbidden_constructs,
        "ast_error": metrics.ast_error,
    }


# ---------------------------------------------------------------------------
# Static movement heuristics
# ---------------------------------------------------------------------------

# Helpers exposed via GameView that indicate the bot navigates toward a goal
_GOAL_HELPERS = frozenset(
    [
        "on_resource",
        "can_gather",
        "nearest_station",
        "has_resource_at",
        "resource_tiles",
        "adjacent_stations",
        "stations",
        "is_boss_adjacent",
    ]
)

# Helpers that guard against walking into obstacles
_WALKABLE_HELPERS = frozenset(["is_walkable", "is_obstacle", "is_inside"])


def analyze_movement_static(bot_path: Path) -> dict[str, Any]:
    """Inspect *bot_path* for movement-quality code patterns.

    Returns a dict with boolean flags and line hints.  All values default to
    ``False`` / ``None`` when the file cannot be parsed or the analysis is
    not applicable.
    """
    empty: dict[str, Any] = {
        "no_walkable_check": False,
        "constant_action_return": False,
        "no_target_logic": False,
        "missing_fallback": False,
        "make_turn_line": None,
    }
    try:
        source = bot_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(bot_path))
    except Exception:  # noqa: BLE001
        return empty

    analyzer = _MovementStaticAnalyzer()
    analyzer.visit(tree)
    return analyzer.result()


class _MovementStaticAnalyzer(ast.NodeVisitor):
    """Single-pass visitor that collects movement code-quality signals."""

    def __init__(self) -> None:
        self._called_names: set[str] = set()
        self._make_turn_node: ast.FunctionDef | None = None
        self._make_turn_has_branch: bool = False
        self._make_turn_returns: list[ast.Return] = []
        self._make_turn_line: int | None = None
        self._all_function_defs: list[ast.FunctionDef] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._all_function_defs.append(node)
        if node.name == "make_turn":
            self._make_turn_node = node
            self._make_turn_line = node.lineno
            self._make_turn_has_branch = any(
                isinstance(child, (ast.If, ast.For, ast.While, ast.Match))
                for child in ast.walk(node)
            )
            self._make_turn_returns = [
                child
                for child in ast.walk(node)
                if isinstance(child, ast.Return)
            ]
        self.generic_visit(node)

    # Also handle class-based bots that use make_turn as a method
    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_Call(self, node: ast.Call) -> None:
        name = _call_name(node)
        if name:
            self._called_names.add(name)
        self.generic_visit(node)

    def result(self) -> dict[str, Any]:
        # no_walkable_check: none of the obstacle guards are called anywhere
        no_walkable_check = not bool(self._called_names & _WALKABLE_HELPERS)

        # constant_action_return: make_turn exists, has no branching, and all
        # returns are string literals
        constant_action_return = False
        if self._make_turn_node and not self._make_turn_has_branch:
            if self._make_turn_returns and all(
                isinstance(r.value, ast.Constant)
                and isinstance(r.value.value, str)
                for r in self._make_turn_returns
                if r.value is not None
            ):
                constant_action_return = True

        # no_target_logic: no goal helper is called anywhere in the file
        no_target_logic = not bool(self._called_names & _GOAL_HELPERS)

        # missing_fallback: make_turn exists, calls a move toward target but
        # has no WAIT branch — heuristic: "WAIT" never appears as a string
        # constant in a return anywhere in the file
        missing_fallback = False
        if self._make_turn_node and not constant_action_return:
            wait_returned = any(
                isinstance(r.value, ast.Constant)
                and r.value.value == "WAIT"
                for fn in self._all_function_defs
                for r in ast.walk(fn)
                if isinstance(r, ast.Return) and r.value is not None
            )
            if not wait_returned and not no_target_logic:
                missing_fallback = True

        return {
            "no_walkable_check": no_walkable_check,
            "constant_action_return": constant_action_return,
            "no_target_logic": no_target_logic,
            "missing_fallback": missing_fallback,
            "make_turn_line": self._make_turn_line,
        }


def _call_name(node: ast.Call) -> str | None:
    """Return the bare attribute or function name from a Call node."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None
