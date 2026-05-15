---
phase_id: phase-0
status: not_started
depends_on: []
source_plan: PLAN.md §5, §9, §20
---

> **PHASE_STATUS:** `NOT_STARTED`

# Phase 0 — Project foundation

## Goal

Bootstrap the repository so later phases can add engine code, scenarios, and tests without re-deciding layout, dependencies, or configuration format.

## Prerequisites

- Python 3.12+ installed
- `uv` or `pip` for dependency management
- Git repository initialized (already present)

## Setup

1. Create and activate a virtual environment at the repo root:

   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Unix
   source .venv/bin/activate
   ```

2. Choose **uv** (preferred) or **pip** and stick to it for all later phases.

## Implementation steps

1. **Add `pyproject.toml`** at the repo root with:
   - Project name (e.g. `code-scenarios`)
   - `requires-python = ">=3.12"`
   - Package discovery for `engine` (empty package OK for now)
   - Console script entry point placeholder: `code-scenarios = "engine.cli:main"` (implement CLI in Phase 1)

2. **Pin minimal dependencies** from [PLAN.md §20](../PLAN.md#20-recommended-minimal-dependency-set):
   - `pygame-ce`
   - `pytest`
   - `ruff`
   - `radon`
   - `tomli` (or use stdlib `tomllib` on 3.12+ only — document choice)
   - `pydantic`
   - Optional dev: `rich`

3. **Create directory scaffold** per [PLAN.md §5](../PLAN.md#5-proposed-system-architecture):

   ```text
   engine/
     __init__.py
     core/
       __init__.py
     simulation/
       __init__.py
     sandbox/
       __init__.py
     scoring/
       __init__.py
     analysis/
       __init__.py
   scenarios/
   student_bots/
   ai/
   ui/
   configs/
   results/
   tests/
   ```

4. **Add `configs/default.toml`** stub per [PLAN.md §9](../PLAN.md#9-configuration-system):

   ```toml
   [engine]
   turn_timeout_ms = 100
   max_turns = 300

   [analysis]
   enable_ai = false
   enable_static_analysis = true
   ```

5. **Expand `.gitignore`** at repo root:
   - `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.ruff_cache/`
   - `results/` (generated sessions; keep folder via `.gitkeep` if desired)

6. **Add `results/.gitkeep`** (optional) so the results directory exists in git without committing session data.

7. **Add root `README.md`** (project README, not this folder) with:
   - One-paragraph project purpose (from PLAN §1)
   - How to install: `uv sync` or `pip install -e ".[dev]"`
   - How to run tests: `uv run pytest` or `pytest`
   - Pointer to `implementation/README.md` for build phases

8. **Add `tests/test_smoke.py`** — minimal test that imports `engine` and asserts `True` (or version attribute once defined).

9. **Add `engine/cli.py`** stub with `main()` that prints usage/help (full CLI in Phase 1).

10. **Configure Ruff** in `pyproject.toml` (`[tool.ruff]`) with sensible defaults for a small library.

11. **Install dependencies** and confirm import path:

    ```bash
    uv sync
    uv run python -c "import engine; print('ok')"
    ```

## Out of scope

- Game loop, scenarios, sandbox, or Pygame UI (Phases 1–2)
- Static analysis or scoring logic (Phase 3)
- Populating `student_bots/` with real bots beyond a `.gitkeep` (Phase 1)

## Definition of done

- [ ] `pyproject.toml` exists with Python 3.12+ and dependencies from PLAN §20
- [ ] Directory layout matches PLAN §5 (all packages have `__init__.py`)
- [ ] `configs/default.toml` exists with `[engine]` and `[analysis]` sections
- [ ] `.gitignore` excludes venv, caches, and `results/` session output
- [ ] Root `README.md` documents install and test commands
- [ ] `tests/test_smoke.py` passes
- [ ] `engine.cli:main` entry point is declared (stub OK)
- [ ] `uv run pytest` or `pytest` exits 0

## Verification

```bash
uv sync
uv run pytest tests/test_smoke.py -v
uv run python -c "import engine; import engine.core"
uv run code-scenarios --help
```

If not using `uv`, replace `uv run` with activated-venv equivalents.

## References

- [PLAN.md §5 — Proposed System Architecture](../PLAN.md#5-proposed-system-architecture)
- [PLAN.md §9 — Configuration System](../PLAN.md#9-configuration-system)
- [PLAN.md §20 — Recommended Minimal Dependency Set](../PLAN.md#20-recommended-minimal-dependency-set)
