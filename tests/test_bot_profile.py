"""Bot display name and icon loading."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from engine.core.bot_profile import read_profile_from_module, validate_icon_path
from engine.core.loader import BotLoadError, load_bot


def test_load_bot_display_name() -> None:
    bot = load_bot(Path("student_bots/resource_wars/example_bot.py"))
    assert bot.player.display_name == "Explorer"


def test_invalid_icon_path_raises(tmp_path: Path) -> None:
    bot_file = tmp_path / "bad_icon_bot.py"
    bot_file.write_text(
        'BOT_ICON = "/etc/passwd"\ndef make_turn(s): return "WAIT"\n',
        encoding="utf-8",
    )
    with pytest.raises(BotLoadError, match="inside project"):
        load_bot(bot_file)


def test_missing_icon_file_raises(tmp_path: Path) -> None:
    bot_file = tmp_path / "student_bots" / "ghost.py"
    bot_file.parent.mkdir(parents=True)
    bot_file.write_text(
        'BOT_ICON = "student_bots/no_such_icon.png"\ndef make_turn(s): return "WAIT"\n',
        encoding="utf-8",
    )
    with pytest.raises(BotLoadError, match="not found"):
        load_bot(bot_file)


def test_read_profile_valid_icon(tmp_path: Path) -> None:
    root = tmp_path
    icon = root / "ui" / "assets" / "icons" / "test.png"
    icon.parent.mkdir(parents=True)
    icon.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    bot_file = root / "student_bots" / "icon_bot.py"
    bot_file.parent.mkdir()
    bot_file.write_text(
        'BOT_DISPLAY_NAME = "Sparky"\n'
        'BOT_ICON = "ui/assets/icons/test.png"\n'
        "def make_turn(s): return 'WAIT'\n",
        encoding="utf-8",
    )
    spec = importlib.util.spec_from_file_location("icon_bot", bot_file)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    name, icon_path = read_profile_from_module(module, bot_file=bot_file, root=root)
    assert name == "Sparky"
    assert icon_path is not None
    resolved = validate_icon_path("ui/assets/icons/test.png", bot_file=bot_file, root=root)
    assert resolved == icon.resolve()
