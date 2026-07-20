"""Subprocess sandbox for student make_turn calls."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

from engine.core.action import Action, parse_action
from engine.core.config import AppConfig
from engine.paths import is_frozen, subprocess_no_window_kwargs
from engine.sandbox.constants import SANDBOX_WORKER_FLAG

DEFAULT_TIMEOUT_ACTION = Action.WAIT


def _spawn_command(bot_path: Path) -> list[str]:
    if is_frozen():
        return [sys.executable, SANDBOX_WORKER_FLAG, str(bot_path)]
    return [sys.executable, "-m", "engine.sandbox.worker_loop", str(bot_path)]


class SandboxedBot:
    """One child process per game; enforces per-turn wall-clock timeout on make_turn only."""

    def __init__(self, bot_path: Path, config: AppConfig) -> None:
        self._bot_path = bot_path.resolve()
        self._config = config
        self._timeout_sec = config.engine.turn_timeout_ms / 1000.0
        self._proc: subprocess.Popen[str] | None = None
        self._start_worker()

    def _start_worker(self) -> None:
        self._proc = subprocess.Popen(
            _spawn_command(self._bot_path),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            **subprocess_no_window_kwargs(),
        )

    def _readline_with_timeout(self, timeout_sec: float) -> dict[str, Any] | None:
        assert self._proc is not None
        assert self._proc.stdout is not None
        result: list[str] = []
        error: list[Exception] = []

        def read() -> None:
            try:
                line = self._proc.stdout.readline()
                if line:
                    result.append(line)
            except Exception as exc:  # noqa: BLE001
                error.append(exc)

        thread = threading.Thread(target=read, daemon=True)
        thread.start()
        thread.join(timeout_sec)
        if thread.is_alive():
            return None
        if error:
            return {"error": str(error[0])}
        if not result:
            return None
        try:
            return json.loads(result[0])
        except json.JSONDecodeError:
            return {"error": "invalid_json"}

    def run_turn(self, game_state: dict[str, Any]) -> tuple[Action, list[str], float]:
        events: list[str] = []
        started = time.perf_counter()
        if self._proc is None or self._proc.poll() is not None:
            self._restart_worker()
        assert self._proc is not None

        if self._proc.poll() is not None:
            events.append("sandbox_dead")
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            return DEFAULT_TIMEOUT_ACTION, events, elapsed_ms

        assert self._proc.stdin is not None
        try:
            self._proc.stdin.write(json.dumps(game_state) + "\n")
            self._proc.stdin.flush()
        except OSError as exc:
            events.append(f"sandbox_write_error:{exc}")
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            return DEFAULT_TIMEOUT_ACTION, events, elapsed_ms

        data = self._readline_with_timeout(self._timeout_sec)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        if data is None:
            self._restart_worker()
            events.append("sandbox_timeout")
            return DEFAULT_TIMEOUT_ACTION, events, elapsed_ms

        if data.get("error"):
            events.append(f"bot_error:{data['error']}")
            return DEFAULT_TIMEOUT_ACTION, events, elapsed_ms

        try:
            return parse_action(data["action"]), events, elapsed_ms
        except (KeyError, ValueError) as exc:
            events.append(f"invalid_action:{exc}")
            return DEFAULT_TIMEOUT_ACTION, events, elapsed_ms

    def _restart_worker(self) -> None:
        self.close()
        self._start_worker()

    def close(self) -> None:
        if self._proc is None or self._proc.poll() is not None:
            self._proc = None
            return
        try:
            if self._proc.stdin:
                self._proc.stdin.close()
        except OSError:
            pass
        try:
            self._proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            self._proc.kill()
        self._proc = None


def run_turn_sandboxed(
    bot_path: Path,
    game_state: dict[str, Any],
    config: AppConfig,
    session: SandboxedBot | None = None,
) -> tuple[Action, list[str], float, SandboxedBot | None]:
    """Execute make_turn with timeout. Reuse session across turns when provided."""
    if session is None:
        session = SandboxedBot(bot_path, config)
    action, events, elapsed_ms = session.run_turn(game_state)
    return action, events, elapsed_ms, session
