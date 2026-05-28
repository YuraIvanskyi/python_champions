"""Localization catalog and translate API."""

from __future__ import annotations

from engine.i18n import (
    map_preset_name,
    normalize_lang,
    scenario_display_name,
    translate,
)
from engine.analysis.feedback import generate_feedback_items


def test_normalize_lang() -> None:
    assert normalize_lang("uk") == "uk"
    assert normalize_lang("en") == "en"
    assert normalize_lang(None) == "en"
    assert normalize_lang("fr") == "en"


def test_translate_en_uk() -> None:
    assert "Run Match" in translate("menu.run_match", lang="en")
    assert "Запустити" in translate("menu.run_match", lang="uk")


def test_translate_format() -> None:
    assert translate("menu.error_max_bots", lang="en", max_p=8, scenario_id="x", count=9) == (
        "At most 8 bots for x (got 9)."
    )


def test_translate_fallback_to_en() -> None:
    assert translate("nonexistent.key", lang="uk") == "nonexistent.key"


def test_scenario_and_map_names() -> None:
    assert scenario_display_name("boss_fight", "uk") == "Бій з босом"
    assert map_preset_name("resource_wars", 0, "uk") == "Поляна"


def test_opponent_desc_energy_stations() -> None:
    key = "menu.opponent_desc.energy_stations.greedy"
    assert translate(key, lang="en") != key
    assert translate(key, lang="uk") != key


def test_feedback_uk_title() -> None:
    static = {"max_complexity": 12, "ruff": [], "forbidden_constructs": [], "functions": []}
    items = generate_feedback_items(static=static, runtime={"timeout_count": 0}, language="uk")
    titles = {it.title for it in items}
    assert "Висока складність" in titles
