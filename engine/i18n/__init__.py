"""Keyed string catalogs for en / uk localization."""

from __future__ import annotations

import logging
from typing import Any, Literal

from engine.i18n.messages_en import MESSAGES_EN
from engine.i18n.messages_uk import MESSAGES_UK

Lang = Literal["en", "uk"]

_CATALOGS: dict[str, dict[str, str]] = {
    "en": MESSAGES_EN,
    "uk": MESSAGES_UK,
}


_log = logging.getLogger(__name__)


class _FormatDefaults(dict[str, Any]):
    """Missing placeholders render as empty text instead of leaking ``{name}``."""

    def __missing__(self, key: str) -> str:
        _log.warning("translate: missing format argument %r", key)
        return ""


def normalize_lang(lang: str | None) -> Lang:
    if lang == "uk":
        return "uk"
    return "en"


def translate(key: str, *, lang: str = "en", **kwargs: Any) -> str:
    """Return localized string; fall back to English, then the key."""
    code = normalize_lang(lang)
    # `in` (not truthiness): an empty string is a valid translation.
    if key in _CATALOGS[code]:
        text = _CATALOGS[code][key]
    else:
        text = _CATALOGS["en"].get(key, key)
    if kwargs:
        try:
            return text.format_map(_FormatDefaults(kwargs))
        except (IndexError, ValueError):
            _log.warning("translate: bad format string for key %r", key)
            return text
    return text


def plural_suffix(count: int, *, lang: str = "en") -> str:
    """Word ending for *count* from the ``feedback.plural.{one,few,many}`` entries.

    en: 1 -> one, else many. uk: 1, 21 -> one; 2-4, 22-24 -> few; 0, 5-20, 25-30 -> many.
    """
    n = abs(int(count))
    if normalize_lang(lang) == "uk":
        if n % 10 == 1 and n % 100 != 11:
            form = "one"
        elif 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
            form = "few"
        else:
            form = "many"
    else:
        form = "one" if n == 1 else "many"
    return translate(f"feedback.plural.{form}", lang=lang)


def t(key: str, *, lang: str = "en", **kwargs: Any) -> str:
    """Alias for translate."""
    return translate(key, lang=lang, **kwargs)


def scenario_display_name(scenario_id: str, lang: str = "en") -> str:
    legacy = {"energy_stations": "mana_pools"}
    scenario_id = legacy.get(scenario_id, scenario_id)
    key = f"scenario.{scenario_id}.name"
    name = translate(key, lang=lang)
    if name != key:
        return name
    return scenario_id.replace("_", " ").title()


def map_preset_name(scenario_id: str, index: int, lang: str = "en") -> str:
    key = f"map.{scenario_id}.{index}"
    name = translate(key, lang=lang)
    if name != key:
        return name
    return translate("map.fallback", lang=lang, index=index)


def category_label(category: str, lang: str = "en") -> str:
    key = f"category.{category}"
    label = translate(key, lang=lang)
    return label if label != key else category.upper()
