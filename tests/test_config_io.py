"""Tests for config save/load and settings validation."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import pytest

from engine.core.config import AppConfig, LocaleConfig, load_config
from engine.core.config_io import (
    SettingsValidationError,
    config_write_path,
    load_config_from_disk,
    save_app_config,
    save_scenario_settings,
    scenario_toml_read_path,
    scenario_toml_write_path,
    validate_scenario_field,
    write_toml,
)
from engine.core.scenario_config import load_scenario_section


def test_load_config_includes_locale() -> None:
    cfg = load_config(Path("configs/default.toml"))
    assert cfg.locale.language == "en"


def test_app_config_save_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = tmp_path / "default.toml"
    monkeypatch.setattr(
        "engine.core.config_io.config_write_path",
        lambda: out,
    )

    cfg = load_config(Path("configs/default.toml"))
    cfg.locale = LocaleConfig(language="uk")
    cfg.ai.model = "phi3:mini"
    save_app_config(cfg)

    monkeypatch.setattr(
        "engine.core.config_io.resolve_config_path",
        lambda explicit=None: out if explicit is None else explicit,
    )
    reloaded = load_config_from_disk()
    assert reloaded.locale.language == "uk"
    assert reloaded.ai.model == "phi3:mini"
    assert reloaded.engine.turn_timeout_ms == cfg.engine.turn_timeout_ms


def test_write_toml_nested_sections(tmp_path: Path) -> None:
    data = {
        "engine": {"turn_timeout_ms": 100, "max_turns": 50},
        "locale": {"language": "en"},
        "ui": {
            "tile_size": 40,
            "map_presets": {
                "seeds": [1, 2],
                "scenario_names": {"resource_wars": ["A", "B"]},
            },
        },
    }
    path = tmp_path / "out.toml"
    write_toml(path, data)
    parsed = tomllib.loads(path.read_text(encoding="utf-8"))
    assert parsed["locale"]["language"] == "en"
    assert parsed["ui"]["map_presets"]["scenario_names"]["resource_wars"] == ["A", "B"]


def test_scenario_save_merges_scenario_section_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundled = Path("scenarios/boss_fight/scenario.toml")
    with bundled.open("rb") as handle:
        original = tomllib.load(handle)

    out = tmp_path / "scenarios" / "boss_fight" / "scenario.toml"
    monkeypatch.setattr(
        "engine.core.config_io.scenario_toml_read_path",
        lambda _sid: bundled,
    )
    monkeypatch.setattr(
        "engine.core.config_io.scenario_toml_write_path",
        lambda _sid: out,
    )

    save_scenario_settings("boss_fight", {"map_width": 14, "max_turns": 250})

    saved = tomllib.load(out.open("rb"))
    assert saved["scenario"]["map_width"] == 14
    assert saved["scenario"]["max_turns"] == 250
    assert saved["boss"] == original["boss"]
    assert saved["scoring"] == original["scoring"]


def test_frozen_config_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    exe = tmp_path / "CodeScenarios.exe"
    exe.write_bytes(b"")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe))
    from engine import paths

    paths.writable_root.cache_clear()
    try:
        assert config_write_path() == tmp_path / "configs" / "default.toml"
        assert scenario_toml_write_path("resource_wars") == (
            tmp_path / "scenarios" / "resource_wars" / "scenario.toml"
        )
        assert scenario_toml_read_path("resource_wars").is_file()
    finally:
        paths.writable_root.cache_clear()


def test_validate_scenario_field_rejects_non_integer() -> None:
    with pytest.raises(SettingsValidationError, match="integer"):
        validate_scenario_field("resource_wars", "map_width", "abc")


def test_validate_scenario_field_bounds() -> None:
    with pytest.raises(SettingsValidationError):
        validate_scenario_field("resource_wars", "map_width", "3")
    assert validate_scenario_field("resource_wars", "map_width", "12") == 12


def test_load_scenario_section_reads_boss_fight() -> None:
    section = load_scenario_section("boss_fight")
    assert section["id"] == "boss_fight"
    assert "map_width" in section
