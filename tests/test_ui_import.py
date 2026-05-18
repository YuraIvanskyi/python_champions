"""UI modules import cleanly (headless via SDL dummy driver)."""

from __future__ import annotations

import os


def test_ui_import_with_dummy_display() -> None:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"

    import pygame

    pygame.display.init()

    import ui.app  # noqa: F401
    import ui.render.map_renderer  # noqa: F401
    import ui.screens.menu  # noqa: F401
    import ui.screens.replay  # noqa: F401
    import ui.screens.simulation  # noqa: F401

    pygame.quit()
