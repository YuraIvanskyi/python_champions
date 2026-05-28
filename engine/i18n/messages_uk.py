"""Ukrainian message catalog."""

from __future__ import annotations

from engine.i18n.ai_strings import _ai_uk
from engine.i18n.feedback_strings import _feedback_uk
from engine.i18n.ui_strings import _ui_uk

MESSAGES_UK: dict[str, str] = {}
MESSAGES_UK.update(_ui_uk())
MESSAGES_UK.update(_feedback_uk())
MESSAGES_UK.update(_ai_uk())
