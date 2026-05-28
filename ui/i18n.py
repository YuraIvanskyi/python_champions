"""UI helpers for localization."""

from __future__ import annotations

from engine.i18n import normalize_lang, translate


def app_lang(app: object) -> str:
    return normalize_lang(getattr(app, "config").locale.language)  # type: ignore[attr-defined]


def t(app: object, key: str, **kwargs: object) -> str:
    return translate(key, lang=app_lang(app), **kwargs)
