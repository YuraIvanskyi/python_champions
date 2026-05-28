"""Load scenarios by id."""

from __future__ import annotations

from engine.core.config_io import load_scenario_toml
from engine.core.scenario import ScenarioBase
from engine.paths import resource_path

SCENARIOS_ROOT = resource_path("scenarios")

# Launcher display order (resource_wars is the default / tutorial scenario).
_SCENARIO_DISPLAY_ORDER = ("resource_wars", "boss_fight", "energy_stations")


def create_scenario(
    scenario_id: str,
    seed: int,
    max_turns: int | None = None,
    *,
    player_ids: list[str] | None = None,
    boss_difficulty: int | None = None,
) -> ScenarioBase:
    if scenario_id == "resource_wars":
        from scenarios.resource_wars import ResourceWarsScenario
        return ResourceWarsScenario(seed=seed, max_turns=max_turns, player_ids=player_ids)
    if scenario_id == "boss_fight":
        from scenarios.boss_fight import BossFightScenario
        return BossFightScenario(
            seed=seed,
            max_turns=max_turns,
            player_ids=player_ids,
            difficulty=boss_difficulty,
        )
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
        scenario_id = child.name
        from engine.core.config_io import scenario_toml_read_path

        if not scenario_toml_read_path(scenario_id).is_file():
            continue
        data = load_scenario_toml(scenario_id)
        meta = data.get("scenario", {})
        sid = str(meta.get("id", scenario_id))
        found.append(
            {
                "id": sid,
                "name": str(meta.get("name", sid)),
                "description": str(meta.get("description", "")),
            }
        )

    def _sort_key(entry: dict[str, str]) -> tuple[int, str]:
        sid = entry["id"]
        if sid in _SCENARIO_DISPLAY_ORDER:
            return (_SCENARIO_DISPLAY_ORDER.index(sid), sid)
        return (len(_SCENARIO_DISPLAY_ORDER), sid)

    found.sort(key=_sort_key)
    return found


def scenario_display_name(scenario_id: str) -> str:
    """Human-readable scenario title from registry metadata."""
    for entry in list_scenarios():
        if entry["id"] == scenario_id:
            return entry["name"]
    return scenario_id.replace("_", " ").title()
