# code-scenarios

A lightweight, extensible educational game framework where students write Python code that competes in turn-based scenarios. The engine runs simulations safely, records replays, and (in later phases) scores code quality and provides feedback. Built for teachers, middle/high school students, and programming clubs — local and offline-first.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (preferred) or pip

## Install

With **uv** (recommended):

```bash
uv sync
```

With **pip**:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix: source .venv/bin/activate
pip install -e ".[dev]"
```

## Run tests

```bash
uv run pytest
```

Or with an activated venv: `pytest`

## CLI (stub)

Phase 1 adds full commands. For now:

```bash
uv run code-scenarios --help
```

## Configuration

TOML config lives in `configs/default.toml`. On Python 3.12+ the project uses the stdlib `tomllib` module (no `tomli` dependency).

## Implementation phases

Build status and step-by-step phase plans: [implementation/README.md](implementation/README.md).
