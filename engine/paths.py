"""Resolve bundled resource paths and writable user data locations."""

from __future__ import annotations

import os
import shutil
import sys
from functools import lru_cache
from pathlib import Path


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


@lru_cache(maxsize=1)
def resource_root() -> Path:
    """Directory containing configs/, student_bots/, ui/, scenarios/, etc."""
    if is_frozen():
        return Path(sys._MEIPASS)
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
    """Directory for results/, user configs, and other writable output."""
    if is_frozen():
        local_app = os.environ.get("LOCALAPPDATA")
        if local_app:
            return Path(local_app) / "CodeScenarios"
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def default_results_dir() -> Path:
    return writable_root() / "results"


def ensure_user_data_tree() -> None:
    """Seed bundled configs/scenarios into the user data dir on first frozen run."""
    if not is_frozen():
        return
    root = writable_root()
    root.mkdir(parents=True, exist_ok=True)
    (root / "results").mkdir(parents=True, exist_ok=True)

    user_cfg = root / "configs" / "default.toml"
    bundled_cfg = resource_path("configs", "default.toml")
    if not user_cfg.is_file() and bundled_cfg.is_file():
        user_cfg.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bundled_cfg, user_cfg)

    for scenario_id in ("resource_wars", "boss_fight", "mana_pools"):
        user_toml = root / "scenarios" / scenario_id / "scenario.toml"
        bundled = resource_path("scenarios", scenario_id, "scenario.toml")
        if not user_toml.is_file() and bundled.is_file():
            user_toml.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(bundled, user_toml)


def bundled_executable(name: str) -> str:
    """Resolve a CLI tool shipped beside a frozen build or on PATH."""
    if is_frozen():
        for candidate in (
            Path(sys._MEIPASS) / f"{name}.exe",
            Path(sys._MEIPASS) / name,
            Path(sys.executable).with_name(f"{name}.exe"),
        ):
            if candidate.is_file():
                return str(candidate)
    found = shutil.which(name)
    return found or name
