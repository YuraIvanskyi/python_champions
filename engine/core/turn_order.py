"""Deterministic player action order for scenario turn resolution."""

from __future__ import annotations

from engine.core.action import Action


def ordered_action_player_ids(
    player_ids: list[str],
    actions: dict[str, Action],
) -> list[str]:
    """Apply actions in setup order, not lexicographic id sort."""
    return [pid for pid in player_ids if pid in actions]
