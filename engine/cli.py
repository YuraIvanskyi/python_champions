"""Console entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from engine.core.config import load_config
from engine.core.game import run_game
from engine.core.loader import BotLoadError, load_bot


def _cmd_gui(args: argparse.Namespace) -> int:
    from ui.app import App

    App(results_dir=Path(args.results_dir)).run()
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    bot_path = Path(args.bot)
    try:
        student_bot = load_bot(bot_path)
    except BotLoadError as exc:
        print(f"Error loading bot: {exc}", file=sys.stderr)
        return 1

    config = load_config(Path(args.config) if args.config else None)
    seed = args.seed if args.seed is not None else 42
    results_dir = Path(args.results_dir)

    opponent = args.opponent or config.game.default_opponent
    run_game(
        scenario_id=args.scenario,
        student_bot=student_bot,
        seed=seed,
        config=config,
        results_dir=results_dir,
        opponent_mode=opponent,
        max_turns=config.engine.max_turns,
        write_results=True,
        print_summary=True,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="code-scenarios",
        description=(
            "Educational turn-based game framework — students write Python bots "
            "that compete in predefined scenarios."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run a single simulation")
    run_parser.add_argument("--scenario", default="resource_wars", help="Scenario id")
    run_parser.add_argument("--bot", required=True, help="Path to student bot .py file")
    run_parser.add_argument("--seed", type=int, default=42, help="RNG seed for reproducibility")
    run_parser.add_argument(
        "--opponent",
        choices=("greedy", "dumb"),
        default=None,
        help="Opponent AI: greedy (smart rival) or dumb (rookie practice)",
    )
    run_parser.add_argument(
        "--config",
        default=None,
        help="Path to TOML config (default: configs/default.toml)",
    )
    run_parser.add_argument(
        "--results-dir",
        default="results",
        help="Directory for session output",
    )
    run_parser.set_defaults(func=_cmd_run)

    gui_parser = subparsers.add_parser("gui", help="Launch the Pygame desktop UI")
    gui_parser.add_argument(
        "--results-dir",
        default="results",
        help="Directory for session output",
    )
    gui_parser.set_defaults(func=_cmd_gui)

    parsed = parser.parse_args(argv)
    if parsed.command is None:
        parser.print_help()
        return 0
    return int(parsed.func(parsed))


if __name__ == "__main__":
    sys.exit(main())
