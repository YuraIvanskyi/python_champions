"""Load scenarios by id."""

from __future__ import annotations

import tomllib
from pathlib import Path

from engine.core.scenario import ScenarioBase

SCENARIOS_ROOT = Path(__file__).resolve().parents[2] / "scenarios"


def create_scenario(
    scenario_id: str,
    seed: int,
    max_turns: int | None = None,
    *,
    player_ids: list[str] | None = None,
) -> ScenarioBase:
    if scenario_id == "resource_wars":
        from scenarios.resource_wars import ResourceWarsScenario
        return ResourceWarsScenario(seed=seed, max_turns=max_turns, player_ids=player_ids)
    if scenario_id == "boss_fight":
        from scenarios.boss_fight import BossFightScenario
        return BossFightScenario(seed=seed, max_turns=max_turns, player_ids=player_ids)
    if scenario_id == "energy_stations":
        from scenarios.energy_stations import EnergyStationsScenario
        return EnergyStationsScenario(seed=seed, max_turns=max_turns, player_ids=player_ids)
    raise ValueError(f"Unknown scenario: {scenario_id}")


def list_scenarios() -> list[dict[str, str]]:
    """Discover scenario packages with scenario.toml metadata."""
    found: list[dict[str, str]] = []
    if not SCENARIOS_ROOT.is_dir():
        return found
    for child in sorted(SCENARIOS_ROOT.iterdir()):
        if not child.is_dir():
            continue
        toml_path = child / "scenario.toml"
        if not toml_path.is_file():
            continue
        with toml_path.open("rb") as handle:
            data = tomllib.load(handle)
        meta = data.get("scenario", {})
        scenario_id = str(meta.get("id", child.name))
        found.append(
            {
                "id": scenario_id,
                "name": str(meta.get("name", scenario_id)),
                "description": str(meta.get("description", "")),
            }
        )
    return found
