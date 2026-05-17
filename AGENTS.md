# AGENTS.md — code-scenarios

Guidance for AI agents and contributors building this repository. Authoritative product design lives in [PLAN.md](PLAN.md); executable build steps live in [implementation/](implementation/).

## Project summary

**code-scenarios** is a lightweight, offline educational game framework. Students write Python bots that compete in turn-based scenarios; the engine runs simulations safely, records replays, and (post-MVP) scores code quality and provides feedback.

**Audience:** teachers, middle/high school students, programming clubs.

**Success looks like:** simple student APIs, reproducible tournaments, fast local runs without cloud dependencies, and analysis beginners can understand.

## Tech stack

| Area | Choice | Notes |
| --- | --- | --- |
| Language | Python **3.12+** | Primary implementation language |
| UI | **Pygame CE** | Local desktop; grid/tile visualization |
| Packaging | **uv** (preferred) or **pip** | `pyproject.toml` at repo root |
| Config | **TOML** | `configs/default.toml` |
| Storage | **JSON + filesystem** | `results/` per session; no database |
| Dynamic loading | **importlib** | One `.py` file per student bot |
| Sandbox | **subprocess + timeouts** | Soft isolation first; no Docker in MVP |
| Static analysis | **Ruff**, **Radon**, **ast** | Student bot files only |
| Testing | **pytest** | Standard layout under `tests/` |
| AI (optional) | **Ollama** / OpenAI-compatible API | Phase 4+; off by default |

**Pinned dependencies (Phase 0):** `pygame-ce`, `pytest`, `ruff`, `radon`, `tomli` (or stdlib `tomllib` on 3.12+ — document the choice), `pydantic`. Optional dev: `rich`.

**Avoid unless explicitly requested:** FastAPI, Django, React, Postgres, Redis, Kubernetes, Unity/Godot, Electron, microservices, cloud-only features.

## Architectural principles

1. **Simplicity first** — local runs, plain files, no DB in early phases.
2. **Deterministic simulations** — seeded RNG; same seed + same bots → identical `replay.json`.
3. **Strong separation** — engine, scenarios, student code, analysis, and UI must not duplicate game rules.
4. **Readonly student API** — expose simplified `game_state` dicts; never engine internals.
5. **AI is advisory** — numeric grades come from Phase 3 scoring; LLMs explain metrics only (Phase 4).

## Repository layout

```text
engine/           # Game engine (core, simulation, sandbox, scoring, analysis, tournament)
scenarios/        # Scenario packages (resource_wars, team_battle, …)
student_bots/     # Example and student submission .py files
ai/               # Optional LLM client (Phase 4+)
ui/               # Pygame CE app (Phase 2+)
configs/          # TOML configuration
results/          # Generated sessions (gitignored; use .gitkeep)
tests/            # pytest suite
implementation/   # Phase plans + PHASE_REGISTRY.yaml
PLAN.md           # Full product/architecture plan
```

Console entry point: `code-scenarios` → `engine.cli:main`.

## Implementation workflow (required for agents)

**Before writing feature code**, follow [implementation/README.md](implementation/README.md):

1. Read [implementation/PHASE_REGISTRY.yaml](implementation/PHASE_REGISTRY.yaml) — single source of truth for phase status.
2. Pick the **lowest** phase where `status` is `not_started` and every id in `depends_on` is `done`.
3. Open the matching `Phase_X.md` and execute **Setup → Implementation steps → Verification** in order.
4. When starting a phase: set `status: in_progress` in the registry, phase frontmatter, and `PHASE_STATUS` banner.
5. When done: all Definition of done checkboxes checked, verification commands pass → set `status: done`, set `completed_at` (ISO date), sync all three layers.
6. If a phase is already `done`, **do not re-implement** unless the user asks to redo or extend it.

| Phase | ID | Depends on | Delivers |
| --- | --- | --- | --- |
| 0 | phase-0 | — | Scaffold, `pyproject.toml`, configs, smoke tests |
| 1 | phase-1 | phase-0 | Headless engine, Resource Wars, sandbox, CLI, replay |
| 2 | phase-2 | phase-1 | Pygame UI, replay viewer |
| 3 | phase-3 | phase-1 | Ruff/Radon/AST, scoring, `metrics.json` |
| 4 | phase-4 | phase-3 | Optional Ollama reports |
| 5 | phase-5 | phase-2, phase-3 | Tournament batch + rankings |
| 6 | phase-6 | phase-5 | Teams, fog, communication APIs |

**MVP = phases 0–3** ([PLAN.md §22](PLAN.md#22-recommended-first-mvp)): one grid scenario, student bot API, AI opponent, turns, replay, basic analysis.

**Post-MVP = phases 4–6:** LLM summaries, classroom tournaments, advanced scenarios.

Audit phase banners:

```bash
grep -r "PHASE_STATUS" implementation/
```

## Development commands

Use `uv run …` when the project uses uv; otherwise activate `.venv` and run equivalents.

```bash
# Phase 0+
uv sync
uv run pytest -v
uv run python -c "import engine"

# Phase 1+
uv run code-scenarios run --scenario resource_wars --bot student_bots/example_bot.py --seed 42
uv run code-scenarios --help

# Phase 2+
uv run python -m ui
uv run code-scenarios gui

# Phase 3+
uv run code-scenarios run --scenario resource_wars --bot student_bots/example_bot.py --no-analysis  # if flag exists

# Phase 4+
uv run code-scenarios report --session <id>

# Phase 5+
uv run code-scenarios tournament --scenario resource_wars --bots-dir student_bots --seed 42
```

**Windows:** activate with `.venv\Scripts\activate`. **Unix:** `source .venv/bin/activate`.

## Module responsibilities

| Package | Responsibility |
| --- | --- |
| `engine/core/` | `Game`, `Player`, `Bot`, `Action`, `TurnResult`, scenario interface, loader, CLI orchestration |
| `engine/simulation/` | `Map`, `Entity`, built-in AI, teams/visibility (Phase 6) |
| `engine/sandbox/` | Subprocess execution, timeouts, import restrictions |
| `engine/scoring/` | Gameplay + code quality + weighted `final_score` |
| `engine/analysis/` | Static/runtime metrics, template feedback, optional AI report |
| `engine/tournament/` | Batch runs, rankings, manifest (Phase 5) |
| `scenarios/<name>/` | Rules, map, victory, `scenario.toml` weights |
| `ui/` | Screens and renderers only — call engine, never fork rules |
| `ai/` | Thin OpenAI-compatible client + prompts (Phase 4) |

### Scenario interface

Scenarios implement `ScenarioBase` with `setup()`, `apply_turn(actions)`, `calculate_score()`, `is_finished()`. Phase 6 may add optional hooks (`get_visible_state`, team resources, communication) with **backward-compatible defaults** so `resource_wars` keeps working.

### Student bot API

**Simple API:**

```python
def make_turn(game_state):
    return "MOVE_RIGHT"  # or Action enum/dataclass
```

**Advanced API:**

```python
class StudentBot(BotBase):
    def make_turn(self, state):
        ...
```

`game_state` is a readonly simplified dict (e.g. `position`, `resources`, `visible_tiles`). Document allowed actions per scenario in starter templates and comments.

### Sandbox and security

- Run `make_turn` in a **subprocess** with wall-clock timeout from `configs/default.toml` (`turn_timeout_ms`).
- On timeout: kill process; forfeit turn or safe default action.
- **Denylist imports** such as `os`, `subprocess`, `socket`; document the allowlist for students.
- No filesystem/network from student code in early phases.
- Never weaken sandbox to “make tests pass” without explicit user approval.

### Scoring (Phase 3+)

Default: `final_score = gameplay_score * 0.7 + code_quality * 0.3`, overridable per scenario in `scenario.toml`. AI text must **not** change numeric scores.

## Configuration

Primary file: `configs/default.toml`.

```toml
[engine]
turn_timeout_ms = 100
max_turns = 300

[analysis]
enable_static_analysis = true
enable_ai = false
```

Phase-specific examples: `configs/dev.toml`, `configs/tournament.toml`. Prefer TOML over hardcoding; use **pydantic** or small loaders for validation where the phase plan specifies it.

## Results and sessions

Single run (Phase 1+):

```text
results/session_<timestamp>/
  replay.json    # seed, scenario, turns, scores
  logs.txt
  metrics.json   # Phase 3+
  ai_report.md   # Phase 4+ when enable_ai = true
```

Tournament (Phase 5+):

```text
results/tournament_<timestamp>/
  manifest.json
  rankings.json
  bot_<name>/
    replay.json
    metrics.json
    logs.txt
```

Do not commit generated session data; `results/` is gitignored (`.gitkeep` optional).

## Coding conventions for agents

- **Match existing style** in the file you edit; minimal diffs scoped to the current phase.
- **Python 3.12+** features are fine; keep student-facing APIs beginner-friendly.
- **No duplicate game logic** in `ui/` or CLI — both call `engine.core` / scenarios.
- **Determinism:** pass `seed` through `Game` and scenario RNG; test with repeated `--seed` runs.
- **Errors:** sandbox timeouts and bad bots fail gracefully (log, forfeit, continue in tournaments).
- **Tests:** add pytest coverage for each phase’s verification list; mock network for AI tests.
- **Ruff:** respect `[tool.ruff]` in `pyproject.toml`; run Ruff on project code, not only student bots.
- **Commits:** only when the user asks; when marking a phase done, sync registry + frontmatter + banner in one commit if committing.
- **Docs:** do not add markdown files the user did not request; phase plans already document scope.

### UI (Phase 2+)

- Pixel/grid aesthetic; snap or simple slide per turn — no real-time physics.
- Handle headless CI: `tests/test_ui_import.py` may skip display; document `pytest -m "not display"` if used.
- Show clear messages for sandbox timeout and invalid bot paths.

### Analysis (Phase 3+)

- Run Ruff, Radon, and AST passes on the student bot path after simulation (unless `--no-analysis` or config disables).
- Use **template** feedback strings for common issues; at least five templates before marking Phase 3 done.
- Write structured `metrics.json` with `gameplay`, `static`, `runtime`, `scores`, `feedback`.

### AI (Phase 4+)

- `enable_ai = false` must imply **zero** network calls.
- Prompts include metrics + template feedback only — never full solutions or rewritten student code.
- Label AI output as advisory; fallback to templates when the endpoint is offline.

## Out of scope (unless user overrides)

| Item | Defer to |
| --- | --- |
| Pygame UI | Phase 2 |
| Static analysis / scoring | Phase 3 |
| LLM reports | Phase 4 |
| Tournament mode | Phase 5 |
| Teams / fog / comms | Phase 6 |
| Web stack, Docker sandbox, LAN multiplayer, curriculum DB | PLAN §21 future |

## Technical risks (mitigate proactively)

1. **Unsafe student code** — subprocess + timeout + import restrictions; readonly state.
2. **Overengineering** — one scenario at a time; file-based storage; no networking in MVP.
3. **AI hallucinations** — LLM explains metrics only; teachers grade from `metrics.json` scores.

## Key references

| Document | Use for |
| --- | --- |
| [PLAN.md](PLAN.md) | Vision, architecture, APIs, security, UI, scoring, risks |
| [implementation/README.md](implementation/README.md) | Phase index, status conventions, PLAN cross-links |
| [implementation/PHASE_REGISTRY.yaml](implementation/PHASE_REGISTRY.yaml) | Current phase status |
| [implementation/Phase_X.md](implementation/) | Step-by-step tasks and verification per phase |

When PLAN.md and a `Phase_X.md` disagree on **build steps**, follow the phase file and registry. When they disagree on **product intent**, follow PLAN.md and note the conflict to the user.
