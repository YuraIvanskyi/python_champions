"""Load scenario.toml from bundled or user-writable paths."""

from __future__ import annotations

from typing import Any

from engine.core.config_io import load_scenario_toml


def load_scenario_section(scenario_id: str) -> dict[str, Any]:
    """Return the [scenario] table from scenario.toml."""
    data = load_scenario_toml(scenario_id)
    return dict(data.get("scenario", {}))
