"""Console entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from engine.core.config import AppConfig, load_config
from engine.core.game import run_game
from engine.core.loader import BotLoadError, load_bot, student_player_id_for_path
from engine.core.scenario_registry import create_scenario
from engine.i18n import normalize_lang, translate
from engine.paths import default_results_dir


def _lang(config: AppConfig) -> str:
    return normalize_lang(config.locale.language)


def _cmd_gui(args: argparse.Namespace) -> int:
    from ui.app import App

    results_dir = Path(args.results_dir)
    if args.results_dir == "results":
        results_dir = default_results_dir()
    App(results_dir=results_dir).run()
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    """Regenerate AI report from an existing metrics.json (no re-simulation)."""
    results_dir = Path(args.results_dir)
    session_id: str | None = getattr(args, "session", None)

    if session_id:
        session_dir = results_dir / session_id
    else:
        from engine.core.replay import latest_session_dir

        session_dir = latest_session_dir(results_dir)
        if session_dir is None:
            config = load_config(Path(args.config) if args.config else None)
            print(translate("cli.no_sessions", lang=_lang(config)), file=sys.stderr)
            return 1

    if not session_dir.is_dir():
        config = load_config(Path(args.config) if args.config else None)
        print(
            translate("cli.session_not_found", lang=_lang(config), path=session_dir),
            file=sys.stderr,
        )
        return 1

    if not (session_dir / "metrics.json").is_file():
        config = load_config(Path(args.config) if args.config else None)
        print(
            translate("cli.metrics_not_found", lang=_lang(config), path=session_dir),
            file=sys.stderr,
        )
        return 1

    config = load_config(Path(args.config) if args.config else None)
    lang = _lang(config)

    if not config.analysis.enable_ai:
        print(translate("cli.ai_skipped_disabled", lang=lang))
        return 0

    from engine.analysis.ai_report import generate_report

    path = generate_report(session_dir, config)
    if path is not None:
        print(translate("cli.ai_report_path", lang=lang, path=path))
    else:
        print(translate("cli.ai_skipped", lang=lang))
    return 0


def _cmd_analysis_only(args: argparse.Namespace) -> int:
    bot_path = Path(args.bot)
    config = load_config(Path(args.config) if args.config else None)
    lang = _lang(config)

    if not bot_path.is_file():
        print(translate("cli.bot_not_found", lang=lang, path=bot_path), file=sys.stderr)
        return 1

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
        print(translate("cli.metrics_written", lang=lang, out_dir=out_dir))
    print_analysis_summary(metrics, lang=lang)
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


def _resolve_run_bot_paths(args: argparse.Namespace, *, lang: str) -> list[Path] | None:
    scenario_id = getattr(args, "scenario", "resource_wars")
    _, cap_max = _scenario_player_limits(scenario_id)

    if args.bots_dir:
        if args.bot is not None or args.bots is not None:
            print(translate("cli.bot_conflict_dir", lang=lang), file=sys.stderr)
            return None
        directory = Path(args.bots_dir)
        if not directory.is_dir():
            print(translate("cli.not_directory", lang=lang, path=directory), file=sys.stderr)
            return None
        py_files = sorted(directory.glob("*.py"))
        limit = args.max_bots if args.max_bots is not None else cap_max
        if len(py_files) > limit:
            py_files = py_files[: int(limit)]
        if len(py_files) < 2:
            print(translate("cli.bots_dir_min", lang=lang), file=sys.stderr)
            return None
        return py_files

    if args.bots is not None:
        if args.bot is not None:
            print(translate("cli.bot_bots_conflict", lang=lang), file=sys.stderr)
            return None
        paths = [Path(p) for p in args.bots]
        if len(paths) < 2:
            print(translate("cli.bots_min_two", lang=lang), file=sys.stderr)
            return None
        return paths

    if args.bot is not None:
        return [Path(args.bot)]

    print(translate("cli.specify_bot", lang=lang), file=sys.stderr)
    return None


def _load_bots(paths: list[Path], scenario_id: str, *, lang: str) -> list:
    min_p, max_p = _scenario_player_limits(scenario_id)
    if len(paths) > max_p:
        print(
            translate(
                "cli.max_competitors",
                lang=lang,
                scenario=scenario_id,
                max_p=max_p,
                count=len(paths),
            ),
            file=sys.stderr,
        )
        sys.exit(1)
    resolved = [p.resolve() for p in paths]
    if len(set(resolved)) != len(resolved):
        print(translate("cli.duplicate_paths", lang=lang), file=sys.stderr)
        sys.exit(1)

    bots = []
    if len(paths) == 1:
        bots.append(load_bot(paths[0]))
    else:
        if len(paths) < min_p:
            print(
                translate(
                    "cli.classroom_min",
                    lang=lang,
                    scenario=scenario_id,
                    min_p=min_p,
                    count=len(paths),
                ),
                file=sys.stderr,
            )
            sys.exit(1)
        for index, path in enumerate(paths):
            pid = student_player_id_for_path(path, index)
            bots.append(load_bot(path, player_id=pid))
    return bots


def _cmd_run(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config) if args.config else None)
    lang = _lang(config)

    raw_paths = _resolve_run_bot_paths(args, lang=lang)
    if raw_paths is None:
        return 1

    for path in raw_paths:
        if not path.is_file():
            print(
                translate("cli.bot_file_not_found", lang=lang, path=path),
                file=sys.stderr,
            )
            return 1

    try:
        student_bots = _load_bots(raw_paths, args.scenario, lang=lang)
    except BotLoadError as exc:
        print(translate("cli.bot_load_error", lang=lang, error=exc), file=sys.stderr)
        return 1

    seed = args.seed if args.seed is not None else 42
    results_dir = Path(args.results_dir)

    opponent = args.opponent or config.game.default_opponent
    boss_difficulty = args.boss_difficulty
    run_game(
        scenario_id=args.scenario,
        student_bots=student_bots,
        seed=seed,
        config=config,
        results_dir=results_dir,
        opponent_mode=opponent,
        max_turns=None,
        write_results=True,
        print_summary=True,
        run_analysis=not args.no_analysis,
        boss_difficulty=boss_difficulty,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Educational turn-based game framework — students write Python bots."
    )
    parser.add_argument("--config", default=None, help="Path to config TOML")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run a simulation")
    run_p.add_argument("--scenario", default="resource_wars")
    run_p.add_argument("--bot", default=None)
    run_p.add_argument("--bots", nargs="+", default=None)
    run_p.add_argument("--bots-dir", default=None)
    run_p.add_argument("--max-bots", type=int, default=None)
    run_p.add_argument("--seed", type=int, default=None)
    run_p.add_argument("--opponent", default=None)
    run_p.add_argument("--boss-difficulty", type=int, default=None)
    run_p.add_argument("--results-dir", default="results")
    run_p.add_argument("--no-analysis", action="store_true")
    run_p.set_defaults(func=_cmd_run)

    analyze_p = sub.add_parser("analyze", help="Run analysis only (no simulation)")
    analyze_p.add_argument("--bot", required=True)
    analyze_p.add_argument("--scenario", default="resource_wars")
    analyze_p.add_argument("--output", default=None)
    analyze_p.set_defaults(func=_cmd_analysis_only)

    report_p = sub.add_parser("report", help="Generate AI report from existing session")
    report_p.add_argument("--session", default=None)
    report_p.add_argument("--results-dir", default="results")
    report_p.set_defaults(func=_cmd_report)

    gui_p = sub.add_parser("gui", help="Launch Pygame UI")
    gui_p.add_argument("--results-dir", default="results")
    gui_p.set_defaults(func=_cmd_gui)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
