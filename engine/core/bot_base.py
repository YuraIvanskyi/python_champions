"""Advanced student bot API."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from engine.core.action import Action


class BotBase(ABC):
    @abstractmethod
    def make_turn(self, game_state: dict[str, Any]) -> str | Action:
        """Return an action string or Action enum member."""
