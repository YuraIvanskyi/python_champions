"""Looping background music keyed to the active UI screen."""

from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path

import pygame

from engine.paths import resource_path

logger = logging.getLogger(__name__)

_SOUNDS_DIR = resource_path("ui", "assets", "sounds")


class BgmTrack(Enum):
    MENUS = "game_menus"
    ACTION = "action_phase"
    RESULTS = "results"


_TRACK_FILES: dict[BgmTrack, str] = {
    BgmTrack.MENUS: "game_menus.wav",
    BgmTrack.ACTION: "action_phase.wav",
    BgmTrack.RESULTS: "results.wav",
}

_DEFAULT_VOLUME = 0.45
_CLICK_FILE = "click.wav"
_DEFAULT_CLICK_VOLUME = 0.55


def _ensure_mixer() -> bool:
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44_100, size=-16, channels=2, buffer=512)
        return True
    except pygame.error as exc:
        logger.warning("Audio mixer disabled: %s", exc)
        return False


def track_for_screen(screen: object) -> BgmTrack:
    """Map the active screen (and replay sub-mode) to a music track."""
    from ui.screens.bot_guide import BotGuideScreen
    from ui.screens.coach import CoachScreen
    from ui.screens.menu import MenuScreen
    from ui.screens.replay import ReplayScreen
    from ui.screens.scores import ScoresScreen
    from ui.screens.settings import SettingsScreen
    from ui.screens.simulation import SimulationScreen

    if isinstance(screen, SimulationScreen):
        return BgmTrack.ACTION
    if isinstance(screen, ReplayScreen):
        return BgmTrack.MENUS if screen._pick_mode else BgmTrack.ACTION
    if isinstance(screen, (ScoresScreen, CoachScreen)):
        return BgmTrack.RESULTS
    if isinstance(screen, (MenuScreen, SettingsScreen, BotGuideScreen)):
        return BgmTrack.MENUS
    return BgmTrack.MENUS


class BackgroundMusic:
    """Play and switch looped WAV tracks via pygame.mixer.music."""

    def __init__(self, *, volume: float = _DEFAULT_VOLUME) -> None:
        self._volume = max(0.0, min(1.0, volume))
        self._enabled = False
        self._current: BgmTrack | None = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    def start(self) -> None:
        """Initialize the mixer; safe to call once after pygame.init()."""
        if self._enabled:
            return
        if not _ensure_mixer():
            return
        try:
            pygame.mixer.music.set_volume(self._volume)
            self._enabled = True
            preload_ui_click()
        except pygame.error as exc:
            logger.warning("Background music disabled: %s", exc)

    def sync(self, screen: object) -> None:
        """Start or switch music to match the given screen."""
        if not self._enabled:
            return
        track = track_for_screen(screen)
        if track == self._current and pygame.mixer.music.get_busy():
            return
        path = _track_path(track)
        if path is None:
            return
        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.play(-1)
            self._current = track
        except pygame.error as exc:
            logger.warning("Could not play %s: %s", path.name, exc)

    def stop(self) -> None:
        if not self._enabled:
            return
        pygame.mixer.music.stop()
        self._current = None


def _track_path(track: BgmTrack) -> Path | None:
    path = _SOUNDS_DIR / _TRACK_FILES[track]
    if path.is_file():
        return path
    logger.warning("Missing background music file: %s", path)
    return None


_click_sound: pygame.mixer.Sound | None = None
_click_loaded = False


def preload_ui_click() -> None:
    """Load click.wav once the mixer is ready."""
    global _click_sound, _click_loaded
    if _click_loaded:
        return
    _click_loaded = True
    if not _ensure_mixer():
        return
    path = _SOUNDS_DIR / _CLICK_FILE
    if not path.is_file():
        logger.warning("Missing UI click sound: %s", path)
        return
    try:
        _click_sound = pygame.mixer.Sound(str(path))
        _click_sound.set_volume(_DEFAULT_CLICK_VOLUME)
    except pygame.error as exc:
        logger.warning("Could not load %s: %s", path.name, exc)


def play_ui_click() -> None:
    """Play the shared button-click sample."""
    global _click_sound
    if _click_sound is None:
        preload_ui_click()
    if _click_sound is None:
        return
    try:
        _click_sound.play()
    except pygame.error as exc:
        logger.warning("UI click playback failed: %s", exc)
