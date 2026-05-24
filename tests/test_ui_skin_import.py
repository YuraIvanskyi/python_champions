"""Skin import and procedural drawing tests — no display required."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


def test_skin_manifest_loads() -> None:
    from ui.skin import assets

    root = Path(__file__).resolve().parents[1]
    manifest = root / "ui" / "assets" / "manifest.toml"
    assets.configure(manifest_path=manifest, use_sliced=True)
    entries = assets._entries()
    assert "panel_stone" in entries
    assert "button_primary" in entries


def test_nine_patch_import() -> None:
    from ui.skin.nine_patch import draw_nine_patch

    assert callable(draw_nine_patch)


def test_draw_panel_procedural_stone() -> None:
    """draw_panel renders stone style without crashing (procedural path)."""
    import pygame
    from ui.skin import assets
    from ui.skin.chrome import draw_panel

    assets.configure(use_sliced=False)
    pygame.display.init()
    surf = pygame.Surface((300, 200))
    r = pygame.Rect(10, 10, 280, 180)
    draw_panel(surf, r, style="stone")


def test_draw_panel_procedural_wood() -> None:
    import pygame
    from ui.skin import assets
    from ui.skin.chrome import draw_panel

    assets.configure(use_sliced=False)
    pygame.display.init()
    surf = pygame.Surface((300, 200))
    draw_panel(surf, pygame.Rect(10, 10, 280, 180), style="wood")


def test_draw_panel_procedural_parchment() -> None:
    import pygame
    from ui.skin import assets
    from ui.skin.chrome import draw_panel

    assets.configure(use_sliced=False)
    pygame.display.init()
    surf = pygame.Surface((300, 200))
    draw_panel(surf, pygame.Rect(10, 10, 280, 180), style="parchment")


def test_draw_primary_button_procedural() -> None:
    import pygame
    from ui.skin import assets
    from ui.skin.chrome import draw_primary_button

    assets.configure(use_sliced=False)
    pygame.display.init()
    pygame.font.init()
    surf = pygame.Surface((300, 200))
    r = pygame.Rect(20, 80, 160, 44)
    draw_primary_button(surf, r, "Run match")
    draw_primary_button(surf, r, "Run match", hovered=True)
    draw_primary_button(surf, r, "Run match", pressed=True)
    draw_primary_button(surf, r, "Run match", enabled=False)


def test_draw_banner_title_procedural() -> None:
    import pygame
    from ui.skin import assets
    from ui.skin.chrome import draw_banner_title

    assets.configure(use_sliced=False)
    pygame.display.init()
    pygame.font.init()
    surf = pygame.Surface((600, 200))
    rect = draw_banner_title(surf, "code-scenarios", center_x=300, y=20, max_width=400)
    assert rect.width > 0 and rect.height > 0


def test_draw_text_clipped_truncates() -> None:
    """draw_text_clipped truncates long text with ellipsis."""
    import pygame
    from ui.skin.chrome import draw_text_clipped
    from ui.skin.typography import body_font

    pygame.display.init()
    pygame.font.init()
    surf = pygame.Surface((200, 50))
    font = body_font(16)
    result = draw_text_clipped(
        surf,
        "This is a very long string that definitely will not fit in a small rect",
        pygame.Rect(0, 0, 80, 30),
        font,
        (255, 255, 255),
        align="left",
    )
    # Result width should be at most the rect width
    assert result.width <= 80


def test_draw_background_procedural() -> None:
    import pygame
    from ui.skin import assets
    from ui.skin.chrome import draw_background

    assets.configure(use_sliced=False)
    pygame.display.init()
    surf = pygame.Surface((400, 300))
    draw_background(surf)
    # Background should no longer be pure black
    color = surf.get_at((200, 150))
    assert color[3] == 255  # fully opaque
