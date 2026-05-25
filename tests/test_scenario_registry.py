"""Scenario registry discovery and ordering."""

from __future__ import annotations

from engine.core.scenario_registry import list_scenarios, scenario_display_name


def test_list_scenarios_puts_resource_wars_first() -> None:
    scenarios = list_scenarios()
    assert scenarios, "expected at least one scenario"
    assert scenarios[0]["id"] == "resource_wars"


def test_scenario_display_name_uses_registry_title() -> None:
    assert scenario_display_name("boss_fight") == "Boss Fight"
    assert scenario_display_name("unknown_scenario") == "Unknown Scenario"
