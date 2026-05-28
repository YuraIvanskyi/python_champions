"""Keyed string catalogs for en / uk localization."""

from __future__ import annotations

from typing import Any, Literal

from engine.i18n.messages_en import MESSAGES_EN
from engine.i18n.messages_uk import MESSAGES_UK

Lang = Literal["en", "uk"]

_CATALOGS: dict[str, dict[str, str]] = {
    "en": MESSAGES_EN,
    "uk": MESSAGES_UK,
}


def normalize_lang(lang: str | None) -> Lang:
    if lang == "uk":
        return "uk"
    return "en"


def translate(key: str, *, lang: str = "en", **kwargs: Any) -> str:
    """Return localized string; fall back to English, then the key."""
    code = normalize_lang(lang)
    text = _CATALOGS[code].get(key) or _CATALOGS["en"].get(key) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def t(key: str, *, lang: str = "en", **kwargs: Any) -> str:
    """Alias for translate."""
    return translate(key, lang=lang, **kwargs)


def scenario_display_name(scenario_id: str, lang: str = "en") -> str:
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
