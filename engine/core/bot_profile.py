"""Student bot presentation metadata (display name, icon)."""

from __future__ import annotations

from pathlib import Path
from types import ModuleType
from typing import Any

from engine.core.errors import BotLoadError

ALLOWED_ICON_PREFIXES = (
    "student_bots",
    "ui/assets/icons",
    "ui\\assets\\icons",
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _normalize_relative(path_str: str) -> str:
    return path_str.replace("\\", "/")


def validate_icon_path(raw: str, *, bot_file: Path, root: Path | None = None) -> Path:
    """Resolve icon path; must stay under allowed project roots."""
    root = root or project_root()
    candidate = Path(raw)
    if candidate.is_absolute():
        try:
            resolved = candidate.resolve()
        except OSError as exc:
            raise BotLoadError(f"Invalid icon path: {raw}") from exc
        try:
            resolved.relative_to(root.resolve())
        except ValueError as exc:
            raise BotLoadError(f"Icon path must be inside project: {raw}") from exc
    else:
        beside = (bot_file.parent / candidate).resolve()
        from_root = (root / candidate).resolve()
        if beside.is_file():
            resolved = beside
        elif from_root.is_file():
            resolved = from_root
        else:
            resolved = from_root
        try:
            resolved.relative_to(root.resolve())
        except ValueError as exc:
            raise BotLoadError(f"Icon path must be inside project: {raw}") from exc

    rel = _normalize_relative(str(resolved.relative_to(root.resolve())))
    if not any(rel == prefix or rel.startswith(prefix + "/") for prefix in ALLOWED_ICON_PREFIXES):
        raise BotLoadError(
            f"Icon must be under student_bots/ or ui/assets/icons/: {raw}"
        )
    if not resolved.is_file():
        raise BotLoadError(f"Icon file not found: {raw}")
    return resolved


def read_profile_from_module(
    module: ModuleType,
    *,
    bot_file: Path,
    default_name: str = "You",
    root: Path | None = None,
) -> tuple[str, str | None]:
    """Read BOT_DISPLAY_NAME and BOT_ICON from a loaded student bot module."""
    display_name = default_name
    icon_path: str | None = None

    if hasattr(module, "get_bot_profile") and callable(module.get_bot_profile):
        profile = module.get_bot_profile()
        if not isinstance(profile, dict):
            raise BotLoadError("get_bot_profile() must return a dict")
        if "display_name" in profile:
            display_name = _coerce_name(profile["display_name"], field="display_name")
        if "icon" in profile and profile["icon"]:
            icon_path = str(validate_icon_path(str(profile["icon"]), bot_file=bot_file, root=root))
        return display_name, icon_path

    if hasattr(module, "BOT_DISPLAY_NAME"):
        display_name = _coerce_name(module.BOT_DISPLAY_NAME, field="BOT_DISPLAY_NAME")

    if hasattr(module, "BOT_ICON") and module.BOT_ICON:
        icon_path = str(validate_icon_path(str(module.BOT_ICON), bot_file=bot_file, root=root))

    return display_name, icon_path


def _coerce_name(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BotLoadError(f"{field} must be a non-empty string")
    name = value.strip()
    if len(name) > 32:
        return name[:32]
    return name


def player_dict(
    player_id: str,
    display_name: str,
    icon_path: str | None,
    *,
    is_student: bool = True,
) -> dict[str, Any]:
    return {
        "id": player_id,
        "display_name": display_name,
        "icon": icon_path,
        "is_student": is_student,
    }
