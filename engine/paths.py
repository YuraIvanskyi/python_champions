"""Resolve bundled resource paths for dev, pip install, and frozen executables."""

from __future__ import annotations

import shutil
import sys
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def resource_root() -> Path:
    """Directory containing configs/, student_bots/, ui/, scenarios/, etc."""
    import engine

    return Path(engine.__file__).resolve().parent.parent


def resource_path(*parts: str) -> Path:
    return resource_root().joinpath(*parts)


def resolve_resource(path: str | Path) -> Path:
    """Resolve a config-relative path against the bundled resource root."""
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return resource_path(*candidate.as_posix().split("/"))


def resolve_bot_path(path: str | Path) -> Path:
    """Resolve a student bot path from cwd or bundled student_bots/."""
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate.resolve()
    from_cwd = (Path.cwd() / candidate).resolve()
    if from_cwd.is_file():
        return from_cwd
    bundled = resource_path(*candidate.as_posix().split("/"))
    if bundled.is_file():
        return bundled.resolve()
    return from_cwd


def default_config_path() -> Path:
    return resource_path("configs", "default.toml")


@lru_cache(maxsize=1)
def writable_root() -> Path:
    """Directory for results/ and other user-written output."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def default_results_dir() -> Path:
    return writable_root() / "results"


def bundled_executable(name: str) -> str:
    """Resolve a CLI tool shipped beside a frozen build or on PATH."""
    if getattr(sys, "frozen", False):
        for candidate in (
            Path(sys._MEIPASS) / f"{name}.exe",
            Path(sys._MEIPASS) / name,
            Path(sys.executable).with_name(f"{name}.exe"),
        ):
            if candidate.is_file():
                return str(candidate)
    found = shutil.which(name)
    return found or name
