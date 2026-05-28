"""Read/write TOML configuration for app and scenario settings."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from typing import Any

from engine.core.config import AppConfig
from engine.paths import default_config_path, resource_path, writable_root


def _is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def resolve_config_path(explicit: Path | None = None) -> Path:
    """Path used to load app config."""
    if explicit is not None:
        return explicit
    if _is_frozen():
        user = writable_root() / "configs" / "default.toml"
        if user.is_file():
            return user
    return default_config_path()


def config_write_path() -> Path:
    """Path where app config is saved from the Settings screen."""
    if _is_frozen():
        return writable_root() / "configs" / "default.toml"
    return default_config_path()


def scenario_toml_read_path(scenario_id: str) -> Path:
    """Path to read scenario.toml (user override when frozen, else bundled)."""
    if _is_frozen():
        user = writable_root() / "scenarios" / scenario_id / "scenario.toml"
        if user.is_file():
            return user
    return resource_path("scenarios", scenario_id, "scenario.toml")


def scenario_toml_write_path(scenario_id: str) -> Path:
    """Path where scenario.toml is written from the Settings screen."""
    if _is_frozen():
        return writable_root() / "scenarios" / scenario_id / "scenario.toml"
    return resource_path("scenarios", scenario_id, "scenario.toml")


def load_scenario_toml(scenario_id: str) -> dict[str, Any]:
    """Load full scenario.toml dict (all sections)."""
    path = scenario_toml_read_path(scenario_id)
    with path.open("rb") as handle:
        return tomllib.load(handle)


def save_scenario_settings(scenario_id: str, scenario_updates: dict[str, Any]) -> None:
    """Merge keys into [scenario] and write scenario.toml."""
    data = load_scenario_toml(scenario_id)
    section = data.setdefault("scenario", {})
    section.update(scenario_updates)
    write_path = scenario_toml_write_path(scenario_id)
    write_path.parent.mkdir(parents=True, exist_ok=True)
    write_toml(write_path, data)


def save_app_config(cfg: AppConfig) -> None:
    """Serialize AppConfig to the appropriate default.toml path."""
    path = config_write_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    write_toml(path, cfg.model_dump())


def reload_app_config(app: object) -> AppConfig:
    """Reload config after save and apply UI theme."""
    from ui import theme
    from ui.skin import typography

    cfg = load_config_from_disk()
    app.config = cfg  # type: ignore[attr-defined]
    theme.apply_config(cfg.ui)
    typography.apply_locale(cfg.locale.language)
    if hasattr(app, "_apply_locale_fonts"):
        app._apply_locale_fonts()  # type: ignore[attr-defined]
    return cfg


def load_config_from_disk(path: Path | None = None) -> AppConfig:
    """Load AppConfig using resolve_config_path."""
    config_path = resolve_config_path(path)
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    return AppConfig.model_validate(data)


def write_toml(path: Path, data: dict[str, Any]) -> None:
    """Write a nested dict as TOML text."""
    tables: dict[str, dict[str, Any]] = {}
    _collect_tables(data, "", tables)
    lines: list[str] = []
    for table_name in sorted(tables.keys()):
        if lines:
            lines.append("")
        lines.append(f"[{table_name}]")
        for key, value in tables[table_name].items():
            lines.append(f"{key} = {_format_value(value)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _collect_tables(data: dict[str, Any], prefix: str, out: dict[str, dict[str, Any]]) -> None:
    """Flatten nested dicts into TOML table sections."""
    scalars: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            nested_prefix = f"{prefix}.{key}" if prefix else key
            if _is_leaf_table(value):
                out[nested_prefix] = dict(value)
            else:
                _collect_tables(value, nested_prefix, out)
        else:
            scalars[key] = value
    if scalars:
        table_name = prefix if prefix else "root"
        if table_name == "root":
            out.setdefault("", scalars)
        else:
            out[table_name] = scalars


def _is_leaf_table(d: dict[str, Any]) -> bool:
    """True when all values are scalars or lists (no nested dicts)."""
    return all(not isinstance(v, dict) for v in d.values())


def _format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, list):
        if not value:
            return "[]"
        inner = ", ".join(_format_value(v) for v in value)
        return f"[{inner}]"
    if isinstance(value, dict):
        parts = [f"{k} = {_format_value(v)}" for k, v in value.items()]
        return "{ " + ", ".join(parts) + " }"
    return repr(value)


# ── Settings validation ───────────────────────────────────────────────────────

MAP_MIN, MAP_MAX = 6, 40
MAX_TURNS_MIN, MAX_TURNS_MAX = 10, 1000
COUNT_MAX = 200


class SettingsValidationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def validate_scenario_field(
    scenario_id: str,
    field: str,
    raw: str,
    *,
    lang: str = "en",
) -> int:
    """Parse and validate a numeric scenario setting field."""
    from engine.i18n import normalize_lang, translate

    del scenario_id
    code = normalize_lang(lang)
    label = translate(f"settings.field.{field}", lang=code)
    if label == f"settings.field.{field}":
        label = field
    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise SettingsValidationError(
            translate("error.field_integer", lang=code, field=label)
        ) from exc

    if field in ("map_width", "map_height"):
        if value < MAP_MIN or value > MAP_MAX:
            raise SettingsValidationError(
                translate(
                    "error.field_range", lang=code, field=label, lo=MAP_MIN, hi=MAP_MAX,
                )
            )
        return value
    if field == "max_turns":
        if value < MAX_TURNS_MIN or value > MAX_TURNS_MAX:
            raise SettingsValidationError(
                translate(
                    "error.field_range",
                    lang=code,
                    field=label,
                    lo=MAX_TURNS_MIN,
                    hi=MAX_TURNS_MAX,
                )
            )
        return value
    if field in ("obstacle_count", "resource_count", "pool_count"):
        if value < 0 or value > COUNT_MAX:
            raise SettingsValidationError(
                translate(
                    "error.field_range", lang=code, field=label, lo=0, hi=COUNT_MAX,
                )
            )
        return value
    raise SettingsValidationError(f"Unknown field: {field}")


SCENARIO_SETTINGS_FIELDS: dict[str, list[str]] = {
    "resource_wars": [
        "map_width",
        "map_height",
        "obstacle_count",
        "resource_count",
        "max_turns",
    ],
    "boss_fight": [
        "map_width",
        "map_height",
        "obstacle_count",
        "max_turns",
    ],
    "mana_pools": [
        "map_width",
        "map_height",
        "obstacle_count",
        "pool_count",
        "max_turns",
    ],
}
