"""Child process entry: load bot and run one turn (invoked via python -m)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from engine.core.loader import BotLoadError, load_bot


def main() -> int:
    raw = sys.stdin.read()
    payload = json.loads(raw)
    bot_path = Path(payload["bot_path"])
    game_state = payload["game_state"]

    try:
        bot = load_bot(bot_path)
        result = bot.make_turn(game_state)
        print(json.dumps({"action": str(result)}))
        return 0
    except BotLoadError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    except Exception as exc:  # noqa: BLE001 — isolate student failures
        print(json.dumps({"error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
