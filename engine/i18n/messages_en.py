"""English message catalog."""

from __future__ import annotations

from engine.i18n.ai_strings import _ai_en
from engine.i18n.feedback_strings import _feedback_en
from engine.i18n.ui_strings import _ui_en

MESSAGES_EN: dict[str, str] = {}
MESSAGES_EN.update(_ui_en())
MESSAGES_EN.update(_feedback_en())
MESSAGES_EN.update(_ai_en())
