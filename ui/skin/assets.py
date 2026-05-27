"""Load and cache chrome surfaces from manifest.toml."""

from __future__ import annotations

import logging
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pygame

from engine.paths import resource_path

logger = logging.getLogger(__name__)

_DEFAULT_MANIFEST = resource_path("ui", "assets", "manifest.toml")

_cache: dict[str, pygame.Surface] = {}
_manifest: dict[str, Any] | None = None
_use_sliced = False   # procedural-first; set True only if clean PNGs are provided
_warned: set[str] = set()


@dataclass(frozen=True)
class ChromeEntry:
    key: str
    file: Path
    nine_slice: tuple[int, int, int, int]


def configure(*, manifest_path: Path | None = None, use_sliced: bool = False) -> None:
    global _manifest, _use_sliced, _cache
    _use_sliced = use_sliced
    _cache.clear()
    path = manifest_path or _DEFAULT_MANIFEST
    if path.is_file():
        _manifest = tomllib.loads(path.read_text(encoding="utf-8"))
    else:
        _manifest = {}
        logger.warning("UI manifest not found: %s", path)


def _entries() -> dict[str, ChromeEntry]:
    if _manifest is None:
        configure()
    assert _manifest is not None
    out: dict[str, ChromeEntry] = {}
    chrome_table = _manifest.get("chrome", {})
    if not isinstance(chrome_table, dict):
        return out
    for short, raw in chrome_table.items():
        if not isinstance(raw, dict):
            continue
        file_rel = raw.get("file")
        if not file_rel:
            continue
        ns = raw.get("nine_slice", [8, 8, 8, 8])
        if len(ns) != 4:
            ns = [8, 8, 8, 8]
        out[str(short)] = ChromeEntry(
            key=str(short),
            file=resource_path(*str(file_rel).replace("\\", "/").split("/")),
            nine_slice=(int(ns[0]), int(ns[1]), int(ns[2]), int(ns[3])),
        )
    return out


def get_surface(name: str) -> pygame.Surface | None:
    """Return cached slice surface or None."""
    if not _use_sliced:
        return None
    if name in _cache:
        return _cache[name]
    entry = _entries().get(name)
    if entry is None:
        return None
    if not entry.file.is_file():
        if name not in _warned:
            logger.warning("Missing chrome asset %s (%s)", name, entry.file)
            _warned.add(name)
        return None
    surf = pygame.image.load(str(entry.file)).convert_alpha()
    _cache[name] = surf
    return surf


def nine_slice_for(name: str) -> tuple[int, int, int, int]:
    entry = _entries().get(name)
    if entry is None:
        return (8, 8, 8, 8)
    return entry.nine_slice
