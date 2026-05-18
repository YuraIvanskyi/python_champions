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


class AppConfig(BaseModel):
    engine: EngineConfig = Field(default_factory=EngineConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or Path("configs/default.toml")
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    return AppConfig.model_validate(data)
