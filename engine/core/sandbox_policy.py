"""Unified import/call denylist for student bot sandbox."""

from __future__ import annotations

# Modules blocked at load time (import / from ... import).
DENIED_IMPORTS = frozenset(
    {
        "os",
        "subprocess",
        "socket",
        "sys",
        "shutil",
        "pathlib",
        "importlib",
        "ctypes",
        "multiprocessing",
        "urllib",
        "http",
        "ftplib",
        "pickle",
        "builtins",
    }
)

# Callable names blocked via direct call (eval, exec, __import__, ...).
FORBIDDEN_CALLS = frozenset(
    {
        "eval",
        "exec",
        "__import__",
        "compile",
        "open",
        "input",
        "breakpoint",
    }
)

# Default forbidden imports for static AST analysis (includes call-only names).
DEFAULT_FORBIDDEN_FOR_ANALYSIS = sorted(
    DENIED_IMPORTS | FORBIDDEN_CALLS | {"eval", "exec"}
)
