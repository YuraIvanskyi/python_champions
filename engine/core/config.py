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
    ruff_select: list[str] = Field(default_factory=lambda: ["E", "F", "W"])
    forbidden_imports: list[str] = Field(
        default_factory=lambda: [
            "os",
            "sys",
            "subprocess",
            "socket",
            "pathlib",
            "shutil",
            "eval",
            "exec",
        ]
    )


class AiConfig(BaseModel):
    provider: str = "vllm"
    base_url: str = "http://localhost:8000/v1"
    model: str = "Qwen/Qwen2.5-1.5B-Instruct"
    timeout_seconds: float = 20.0
    max_tokens: int = 400
    health_check_url: str = "http://localhost:8000/health"


class GameConfig(BaseModel):
    default_opponent: str = "greedy"


class UIThemeConfig(BaseModel):
    asset_manifest: str = "ui/assets/manifest.toml"
    use_sliced_assets: bool = False
    game_font: str = "ui/assets/fonts/Jacquard24-Regular.ttf"
    code_font: str = "ui/assets/fonts/FantasqueSansMNerdFontMono-Regular.ttf"


class UICoachConfig(BaseModel):
    max_quest_cards: int = 12
    code_panel_font_pt: int = 14


class UIMapPresetsConfig(BaseModel):
    seeds: list[int] = Field(default_factory=lambda: [7, 23, 42, 58, 91])
    names: list[str] = Field(
        default_factory=lambda: [
            "The Clearing",
            "Obstacle Run",
            "Classic",
            "Open Field",
            "The Maze",
        ]
    )
    scenario_names: dict[str, list[str]] = Field(default_factory=dict)


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
    theme: UIThemeConfig = Field(default_factory=UIThemeConfig)
    coach: UICoachConfig = Field(default_factory=UICoachConfig)
    map_presets: UIMapPresetsConfig = Field(default_factory=UIMapPresetsConfig)


class AppConfig(BaseModel):
    engine: EngineConfig = Field(default_factory=EngineConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    ai: AiConfig = Field(default_factory=AiConfig)
    game: GameConfig = Field(default_factory=GameConfig)
    ui: UIConfig = Field(default_factory=UIConfig)


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or Path("configs/default.toml")
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    return AppConfig.model_validate(data)
