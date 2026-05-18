"""Dynamic student bot loading."""

from __future__ import annotations

import ast
import importlib.util
import inspect
from pathlib import Path
from typing import Any

from engine.core.action import Action
from engine.core.bot_base import BotBase
from engine.core.player import Bot, Player

DENIED_IMPORTS = frozenset(
    {
        "os",
        "subprocess",
        "socket",
        "sys",
        "shutil",
        "pathlib",
        "importlib",
        "ctypes",
        "multiprocessing",
        "urllib",
        "http",
        "ftplib",
        "pickle",
        "builtins",
    }
)


class BotLoadError(Exception):
    pass


def _check_imports(source: str, path: Path) -> None:
    tree = ast.parse(source, filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in DENIED_IMPORTS:
                    raise BotLoadError(f"Import not allowed: {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            if root in DENIED_IMPORTS:
                raise BotLoadError(f"Import not allowed: {node.module}")


def _wrap_make_turn(fn: Any) -> Any:
    def caller(game_state: dict[str, Any]) -> str | Action:
        return fn(game_state)

    return caller


def load_bot(path: Path, player_id: str = "student", display_name: str = "Student") -> Bot:
    if not path.is_file():
        raise BotLoadError(f"Bot file not found: {path}")

    source = path.read_text(encoding="utf-8")
    _check_imports(source, path)

    module_name = f"student_bot_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise BotLoadError(f"Could not load module from {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    player = Player(player_id=player_id, display_name=display_name, is_student=True)

    if hasattr(module, "make_turn") and callable(module.make_turn):
        return Bot(player=player, make_turn=_wrap_make_turn(module.make_turn), source_path=str(path))

    for _name, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, BotBase) and obj is not BotBase:
            instance = obj()
            return Bot(
                player=player,
                make_turn=_wrap_make_turn(instance.make_turn),
                source_path=str(path),
            )

    raise BotLoadError("Bot file must define make_turn(game_state) or a BotBase subclass")
