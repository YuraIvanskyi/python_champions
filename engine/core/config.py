"""TOML configuration loading."""

from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field


class EngineConfig(BaseModel):
    turn_timeout_ms: int = 100
    max_turns: int = 300


class AnalysisConfig(BaseModel):
    enable_ai: bool = False
    enable_static_analysis: bool = True


class GameConfig(BaseModel):
    default_opponent: str = "greedy"


class UIConfig(BaseModel):
    tile_size: int = 40
    map_padding: int = 24
    map_top: int = 16
    window_width: int = 1024
    window_height: int = 800
    margin_x: int = 48
    label_font_pt: int = 14
    hud_title_pt: int = 24
    hud_body_pt: int = 18
    hud_line_spacing: int = 24
    center_title_pt: int = 28
    center_subtitle_pt: int = 16
    footer_pt: int = 15
    menu_hint_pt: int = 15


class AppConfig(BaseModel):
    engine: EngineConfig = Field(default_factory=EngineConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    game: GameConfig = Field(default_factory=GameConfig)
    ui: UIConfig = Field(default_factory=UIConfig)


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or Path("configs/default.toml")
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    return AppConfig.model_validate(data)
