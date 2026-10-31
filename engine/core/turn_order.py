"""Deterministic player action order for scenario turn resolution."""

from __future__ import annotations

from engine.core.action import Action


def ordered_action_player_ids(
    player_ids: list[str],
    actions: dict[str, Action],
) -> list[str]:
    """Apply actions in setup order, not lexicographic id sort."""
    return [pid for pid in player_ids if pid in actions]


def blocked_move_events(
    pid: str,
    cause: str,
    cell: tuple[int, int],
    entered_this_turn: set[tuple[int, int]],
) -> list[str]:
    """Events for a refused MOVE: the plain ``<pid>_blocked`` plus its cause.

    Causes: ``edge``, ``obstacle``, ``unit`` (someone already stood there) and
    ``conflict`` (a unit that entered the same tile earlier in this very turn).
    """
    if cause == "unit" and cell in entered_this_turn:
        cause = "conflict"
    return [f"{pid}_blocked", f"{pid}_blocked_by_{cause}"]
