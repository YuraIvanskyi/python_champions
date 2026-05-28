"""Font loading for the RPG UI skin.

Fonts are resolved from configured paths (set via apply_config in ui/theme.py):
  - game_font_path  → Skranji (en) or Pangolin (uk; Latin + Cyrillic)
  - code_font_path  → FantasqueSansMNerdFontMono (code panel, text fields)

apply_locale() picks the game face from [locale].language after theme loads TOML paths.
Each font is cached per (path, size) so repeated calls are cheap.
"""

from __future__ import annotations

from pathlib import Path

import pygame

from engine.i18n import normalize_lang
from engine.paths import resource_path

_SKRANJI_FONT = resource_path("ui", "assets", "fonts", "Skranji-Regular.ttf")
_PANGOLIN_FONT = resource_path("ui", "assets", "fonts", "Pangolin-Regular.ttf")

# Default game font (English); Ukrainian uses Pangolin via apply_locale
_DEFAULT_GAME_FONT = _SKRANJI_FONT
_DEFAULT_CODE_FONT = resource_path(
    "ui", "assets", "fonts", "FantasqueSansMNerdFontMono-Regular.ttf"
)

_game_font_path: Path = _DEFAULT_GAME_FONT
_code_font_path: Path = _DEFAULT_CODE_FONT

# Per-size caches: (path_str, size) → Font
_game_cache: dict[tuple[str, int], pygame.font.Font] = {}
_code_cache: dict[tuple[str, int], pygame.font.Font] = {}


def set_game_font_path(path: Path | None) -> None:
    """Override the game (title + body) font. Pass None to use default."""
    global _game_font_path, _game_cache
    _game_font_path = path if (path and path.is_file()) else _DEFAULT_GAME_FONT
    _game_cache.clear()


def set_code_font_path(path: Path | None) -> None:
    """Override the code/monospace font. Pass None to use default."""
    global _code_font_path, _code_cache
    _code_font_path = path if (path and path.is_file()) else _DEFAULT_CODE_FONT
    _code_cache.clear()


def apply_locale(language: str) -> None:
    """Set game font from locale: Skranji for English, Pangolin for Ukrainian."""
    lang = normalize_lang(language)
    path = _PANGOLIN_FONT if lang == "uk" else _SKRANJI_FONT
    set_game_font_path(path)


def _load_font(path: Path, size: int, cache: dict[tuple[str, int], pygame.font.Font]) -> pygame.font.Font:
    key = (str(path), size)
    if key not in cache:
        if path.is_file():
            cache[key] = pygame.font.Font(str(path), size)
        else:
            cache[key] = pygame.font.SysFont("segoe ui,arial,sans-serif", size)
    return cache[key]


def title_font(size: int) -> pygame.font.Font:
    """RPG display font for screen titles and banners."""
    return _load_font(_game_font_path, size, _game_cache)


def body_font(size: int) -> pygame.font.Font:
    """RPG display font for labels, HUD text, button labels, and all non-code text."""
    return _load_font(_game_font_path, size, _game_cache)


def code_font(size: int) -> pygame.font.Font:
    """Monospace font for code panels, text fields, and line numbers."""
    return _load_font(_code_font_path, size, _code_cache)
