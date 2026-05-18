"""Sandbox import restrictions (documented denylist)."""

from __future__ import annotations

# Re-exported from loader for student documentation; enforced at load + worker.
DENIED_ROOT_MODULES = (
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
)

ALLOWED_BUILTINS = frozenset(
    {
        "abs",
        "all",
        "any",
        "bool",
        "dict",
        "enumerate",
        "float",
        "int",
        "len",
        "list",
        "max",
        "min",
        "range",
        "round",
        "set",
        "sorted",
        "str",
        "sum",
        "tuple",
        "zip",
        "True",
        "False",
        "None",
    }
)
