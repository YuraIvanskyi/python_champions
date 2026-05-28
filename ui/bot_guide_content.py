"""Scenario-specific bot-writing help shown in the launcher guide screen."""

from __future__ import annotations

from engine.i18n.guides import GuideBlock, guide_blocks_for_scenario as _guide_blocks

__all__ = ["GuideBlock", "guide_blocks_for_scenario"]


def guide_blocks_for_scenario(scenario_id: str, lang: str = "en") -> list[GuideBlock]:
    return _guide_blocks(scenario_id, lang)
