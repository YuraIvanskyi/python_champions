"""Console entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from engine.core.config import load_config
from engine.core.game import run_game
from engine.core.loader import BotLoadError, load_bot, student_player_id_for_path
from engine.core.scenario_registry import create_scenario


def _cmd_gui(args: argparse.Namespace) -> int:
    from ui.app import App

    App(results_dir=Path(args.results_dir)).run()
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    """Regenerate AI report from an existing metrics.json (no re-simulation)."""
    results_dir = Path(args.results_dir)
    session_id: str | None = getattr(args, "session", None)

    if session_id:
        session_dir = results_dir / session_id
    else:
        # Auto-detect the most recent session
        candidates = sorted(results_dir.glob("session_*"))
        if not candidates:
            print("No sessions found in results/.", file=sys.stderr)
            return 1
        session_dir = candidates[-1]

    if not session_dir.is_dir():
        print(f"Session directory not found: {session_dir}", file=sys.stderr)
        return 1

    if not (session_dir / "metrics.json").is_file():
        print(f"metrics.json not found in {session_dir}.", file=sys.stderr)
        return 1

    config = load_config(Path(args.config) if args.config else None)

    if not config.analysis.enable_ai:
        print("AI skipped (disabled or vLLM not reachable) — set enable_ai = true in configs/default.toml")
        return 0

    from engine.analysis.ai_report import generate_report

    path = generate_report(session_dir, config)
    if path is not None:
        print(f"AI report: {path}")
    else:
        print("AI skipped (disabled or vLLM not reachable)")
    return 0


def _cmd_analysis_only(args: argparse.Namespace) -> int:
    bot_path = Path(args.bot)
    if not bot_path.is_file():
        print(f"Bot file not found: {bot_path}", file=sys.stderr)
        return 1

    config = load_config(Path(args.config) if args.config else None)
    from engine.analysis.pipeline import build_metrics, print_analysis_summary, write_metrics

    metrics = build_metrics(
        bot_path=bot_path,
        config=config,
        final_scores={"student": 0, "opponent": 0},
        scenario_id=args.scenario,
        runtime_collector=None,
    )
    if args.output:
        out_dir = Path(args.output)
        out_dir.mkdir(parents=True, exist_ok=True)
        write_metrics(out_dir, metrics)
        print(f"Wrote metrics to {out_dir / 'metrics.json'}")
    print_analysis_summary(metrics)
    return 0


def _scenario_player_limits(scenario_id: str) -> tuple[int, int]:
    """Return (min_players, max_players) for the given scenario."""
    try:
        sc = create_scenario(scenario_id, seed=0)
        fn = getattr(sc.__class__, "player_limits", None)
        if callable(fn):
            return fn()
    except Exception:
        pass
    from scenarios.resource_wars.game import ResourceWarsScenario
    return ResourceWarsScenario.player_limits()


def _resolve_run_bot_paths(args: argparse.Namespace) -> list[Path] | None:
    scenario_id = getattr(args, "scenario", "resource_wars")
    _, cap_max = _scenario_player_limits(scenario_id)

    if args.bots_dir:
        if args.bot is not None or args.bots is not None:
            print(
                "Error: use only one of --bot, --bots, or --bots-dir.",
                file=sys.stderr,
            )
            return None
        directory = Path(args.bots_dir)
        if not directory.is_dir():
            print(f"Error: not a directory: {directory}", file=sys.stderr)
            return None
        py_files = sorted(directory.glob("*.py"))
        limit = args.max_bots if args.max_bots is not None else cap_max
        if len(py_files) > limit:
            py_files = py_files[: int(limit)]
        if len(py_files) < 2:
            print(
                "Error: --bots-dir must contain at least two .py bot files.",
                file=sys.stderr,
            )
            return None
        return py_files

    if args.bots is not None:
        if args.bot is not None:
            print(
                "Error: use either --bot or --bots, not both.",
                file=sys.stderr,
            )
            return None
        paths = [Path(p) for p in args.bots]
        if len(paths) < 2:
            print(
                "Error: --bots requires at least two paths "
                "(use --bot for one student vs built-in AI).",
                file=sys.stderr,
            )
            return None
        return paths

    if args.bot is not None:
        return [Path(args.bot)]

    print(
        "Error: specify --bot, --bots, or --bots-dir.",
        file=sys.stderr,
    )
    return None


def _load_bots(paths: list[Path], scenario_id: str) -> list:
    min_p, max_p = _scenario_player_limits(scenario_id)
    if len(paths) > max_p:
        print(
            f"Error: {scenario_id} allows at most {max_p} competitors (got {len(paths)}).",
            file=sys.stderr,
        )
        sys.exit(1)
    resolved = [p.resolve() for p in paths]
    if len(set(resolved)) != len(resolved):
        print("Error: duplicate bot paths are not allowed.", file=sys.stderr)
        sys.exit(1)

    bots = []
    if len(paths) == 1:
        bots.append(load_bot(paths[0]))
    else:
        if len(paths) < min_p:
            print(
                f"Error: {scenario_id} needs at least {min_p} student bots "
                f"for a classroom match (got {len(paths)}).",
                file=sys.stderr,
            )
            sys.exit(1)
        for index, path in enumerate(paths):
            pid = student_player_id_for_path(path, index)
            bots.append(load_bot(path, player_id=pid))
    return bots


def _cmd_run(args: argparse.Namespace) -> int:
    raw_paths = _resolve_run_bot_paths(args)
    if raw_paths is None:
        return 1

    for path in raw_paths:
        if not path.is_file():
            print(f"Error: bot file not found: {path}", file=sys.stderr)
            return 1

    try:
        student_bots = _load_bots(raw_paths, args.scenario)
    except BotLoadError as exc:
        print(f"Error loading bot: {exc}", file=sys.stderr)
        return 1

    config = load_config(Path(args.config) if args.config else None)
    seed = args.seed if args.seed is not None else 42
    results_dir = Path(args.results_dir)

    opponent = args.opponent or config.game.default_opponent
    run_game(
        scenario_id=args.scenario,
        student_bots=student_bots,
        seed=seed,
        config=config,
        results_dir=results_dir,
        opponent_mode=opponent,
        max_turns=config.engine.max_turns,
        write_results=True,
        print_summary=True,
        run_analysis=not args.no_analysis,
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
    run_parser.add_argument(
        "--bot",
        default=None,
        help="Path to one student bot (.py); plays versus built-in AI opponent",
    )
    run_parser.add_argument(
        "--bots",
        nargs="+",
        default=None,
        metavar="PATH",
        help="Two or more student bot paths; one shared match (students only, no AI)",
    )
    run_parser.add_argument(
        "--bots-dir",
        default=None,
        help="Directory of .py bots (sorted by name); classroom match, students only",
    )
    run_parser.add_argument(
        "--max-bots",
        type=int,
        default=None,
        help="With --bots-dir, cap how many files are loaded (default: scenario max)",
    )
    run_parser.add_argument("--seed", type=int, default=42, help="RNG seed for reproducibility")
    run_parser.add_argument(
        "--opponent",
        choices=("greedy", "dumb"),
        default=None,
        help="Opponent AI when using --bot only: greedy (smart rival) or dumb (rookie practice)",
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
    run_parser.add_argument(
        "--no-analysis",
        action="store_true",
        help="Skip static/runtime analysis and metrics.json",
    )
    run_parser.set_defaults(func=_cmd_run)

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Run static analysis on a bot file without simulating",
    )
    analyze_parser.add_argument("--bot", required=True, help="Path to student bot .py file")
    analyze_parser.add_argument("--scenario", default="resource_wars", help="Scenario id")
    analyze_parser.add_argument(
        "--config",
        default=None,
        help="Path to TOML config (default: configs/default.toml)",
    )
    analyze_parser.add_argument(
        "--output",
        default=None,
        help="Optional directory to write metrics.json",
    )
    analyze_parser.set_defaults(func=_cmd_analysis_only)

    report_parser = subparsers.add_parser(
        "report",
        help="Regenerate AI report from existing metrics.json (no re-simulation)",
    )
    report_parser.add_argument(
        "--session",
        default=None,
        help="Session id (directory name inside --results-dir); defaults to most recent",
    )
    report_parser.add_argument(
        "--results-dir",
        default="results",
        help="Directory containing session folders",
    )
    report_parser.add_argument(
        "--config",
        default=None,
        help="Path to TOML config (default: configs/default.toml)",
    )
    report_parser.set_defaults(func=_cmd_report)

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
