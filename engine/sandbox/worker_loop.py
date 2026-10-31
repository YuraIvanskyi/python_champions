"""Long-lived child: load bot once, serve make_turn requests on stdin (one JSON line per turn)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import TextIO

from engine.core.loader import BotLoadError, load_bot


def _send(channel: TextIO, payload: dict[str, object]) -> None:
    channel.write(json.dumps(payload) + "\n")
    channel.flush()


def main() -> int:
    # Keep the real stdout for the host protocol only. Anything the student prints
    # (at import time or inside make_turn) is discarded so it cannot corrupt the stream.
    protocol = sys.stdout
    sink = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115 - lives for the whole process
    sys.stdout = sink
    sys.stderr = sink

    if len(sys.argv) < 2:
        _send(protocol, {"error": "bot_path required"})
        return 1

    bot_path = Path(sys.argv[1])
    try:
        bot = load_bot(bot_path)
    except BotLoadError as exc:
        _send(protocol, {"error": str(exc)})
        return 1
    except Exception as exc:  # noqa: BLE001
        _send(protocol, {"error": f"{type(exc).__name__}: {exc}"})
        return 1

    # Handshake: the host starts the per-turn clock only after this line.
    _send(protocol, {"ready": True})

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            game_state = json.loads(line)
            result = bot.make_turn(game_state)
            _send(protocol, {"action": str(result)})
        except Exception as exc:  # noqa: BLE001
            _send(protocol, {"error": str(exc)})

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
