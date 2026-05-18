"""Long-lived child: load bot once, serve make_turn requests on stdin (one JSON line per turn)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from engine.core.loader import BotLoadError, load_bot


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "bot_path required"}), flush=True)
        return 1

    bot_path = Path(sys.argv[1])
    try:
        bot = load_bot(bot_path)
    except BotLoadError as exc:
        print(json.dumps({"error": str(exc)}), flush=True)
        return 1

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            game_state = json.loads(line)
            result = bot.make_turn(game_state)
            print(json.dumps({"action": str(result)}), flush=True)
        except Exception as exc:  # noqa: BLE001
            print(json.dumps({"error": str(exc)}), flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
