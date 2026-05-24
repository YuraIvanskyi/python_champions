---
phase_id: phase-4
status: done
depends_on: [phase-3-1]
source_plan: PLAN.md §16 Phase 4, §7, §9, §23
completed_at: "2026-05-24"
---

> **PHASE_STATUS:** `DONE`

# Phase 4 — AI feedback (vLLM)

## Goal

Add **optional local LLM integration** via [vLLM](https://docs.vllm.ai/) to generate readable summaries and teacher-friendly reports from existing metrics — without auto-fixing code or replacing grading ([PLAN.md §16.4](../PLAN.md#16-development-phases), [§7](../PLAN.md#7-ai-integration-strategy)).

vLLM is preferred over Ollama because it achieves significantly higher token throughput on the same hardware through continuous batching and PagedAttention — important for classroom scenarios where multiple bot reports are generated back-to-back.

## Prerequisites

- Phase 3-1 complete (`metrics.json` + feedback templates + Coach screen exist)
- Python 3.12+ environment (separate from project venv is fine)
- NVIDIA GPU recommended; vLLM also runs CPU-only via `--device cpu` (slower)
- Optional: [vLLM](https://docs.vllm.ai/en/latest/getting_started/installation.html) installed and a model downloaded from HuggingFace

## Recommended models

| Tier | Model (HuggingFace ID) | VRAM | Notes |
| --- | --- | --- | --- |
| **Speed** | `Qwen/Qwen2.5-1.5B-Instruct` | ~3 GB | Default; runs well even on small GPUs and CPU |
| **Speed** | `microsoft/Phi-3.5-mini-instruct` | ~4 GB | Excellent instruction-following for feedback |
| **Balanced** | `Qwen/Qwen2.5-7B-Instruct` | ~8 GB | Richer analysis; recommended when GPU ≥ 8 GB |
| **Balanced** | `google/gemma-2-2b-it` | ~5 GB | Good quality at 2B scale |

The **Speed** tier is the default config. Teachers can switch to Balanced in `configs/default.toml`.

## Setup

### 1 — Extend `configs/default.toml`

```toml
[analysis]
enable_ai = false            # flip to true once vLLM is running

[ai]
provider      = "vllm"
base_url      = "http://localhost:8000/v1"
model         = "Qwen/Qwen2.5-1.5B-Instruct"
timeout_seconds = 20
max_tokens    = 400
health_check_url = "http://localhost:8000/health"
```

### 2 — Create `ai/` package files

- `ai/__init__.py`
- `ai/client.py` — OpenAI-compatible HTTP client with health-check and graceful fallback
- `ai/prompts.py` — system/user prompt templates (no raw engine internals, no full solutions)
- `ai/health.py` — synchronous connectivity probe used by both CLI and UI

### 3 — vLLM server quick-start (documented for teachers)

```bash
# Install vLLM (do once, outside project venv)
pip install vllm

# Speed tier — runs on any CUDA GPU ≥ 3 GB or CPU
vllm serve Qwen/Qwen2.5-1.5B-Instruct --max-model-len 4096

# Balanced tier — GPU ≥ 8 GB recommended
vllm serve Qwen/Qwen2.5-7B-Instruct --max-model-len 4096

# CPU-only fallback (slow but functional)
vllm serve Qwen/Qwen2.5-1.5B-Instruct --device cpu --max-model-len 2048
```

The server exposes an OpenAI-compatible endpoint at `http://localhost:8000/v1`.

## Implementation steps

### Step 1 — Health probe (`ai/health.py`)

- `is_vllm_reachable(base_url: str, timeout: float = 3.0) -> bool`
  - GET `{health_check_url}` (200 → reachable)
  - Catch `ConnectionRefusedError`, `TimeoutError`, any `requests`/`httpx` error → return `False`
- `get_loaded_model(base_url: str) -> str | None`
  - GET `{base_url}/models` → parse first model id; `None` on failure
- Called before every AI generation attempt; result cached for the session (re-checked only on manual retry)

### Step 2 — AI client (`ai/client.py`)

- Read config from TOML via existing engine config loader
- `complete(system: str, user: str) -> str | None`:
  - If `enable_ai = false` → return `None` immediately (zero-cost path)
  - Call `is_vllm_reachable()` → if `False` → return `None`, log warning
  - POST to `{base_url}/chat/completions` with `model`, `max_tokens`, `timeout_seconds`
  - On `TimeoutError` or HTTP error → return `None`, log warning
  - On success → return assistant message text
- No API keys stored in repo; document env var `OPENAI_API_KEY` comment placeholder if using cloud endpoint (unused by default)

### Step 3 — Prompts (`ai/prompts.py`)

Guard rails from [PLAN.md §7](../PLAN.md#7-ai-integration-strategy) and [§23.3](../PLAN.md#23-biggest-technical-risks):

- **System prompt** must:
  - State the AI is an educational code analysis assistant
  - Explicitly forbid generating full solutions or rewriting student code
  - Limit response to a short summary (≤ 5 sentences for student, ≤ 3 bullet points for teacher notes)
- **User prompt** contains only:
  - Scenario name and turn count
  - Gameplay score, code quality score, final weighted score
  - List of feedback template strings (from `metrics.json`)
  - Top 2–3 most severe Ruff rule IDs with line counts
  - **Never** raw engine internals, class internals, or full source code

### Step 4 — Report generator (`engine/analysis/ai_report.py`)

- Entry point: `generate_report(session_dir: Path, config: dict) -> Path | None`
- If `enable_ai = false` → return `None`
- If health check fails → log `"vLLM not reachable — skipping AI report"` → return `None`
- Load `metrics.json`, build prompts, call `ai/client.py`
- Write `results/session_*/ai_report.md` with:
  ```
  > ⚠️ AI-generated summary — advisory only. Numeric scores come from static analysis.

  **Student summary:** …

  **Teacher notes:** …
  ```
- On any failure (network, model error, unexpected exception) → log warning → return `None`; never raise to caller

### Step 5 — CLI integration

- `code-scenarios run …` calls `generate_report()` after simulation when `enable_ai = true`
- `code-scenarios report --session <id>` regenerates AI text from **existing** `metrics.json` without re-simulating; prints path to `ai_report.md` or `"AI skipped (disabled or vLLM not reachable)"`

### Step 6 — In-game vLLM setup screen (`ui/screens/vllm_setup.py`)

This screen is shown inside the Coach screen's "AI Summary" tab whenever `enable_ai = true` but the health probe returns `False`. It teaches users how to start vLLM without leaving the game.

Content to display (styled with the existing RPG skin — `ui/skin`, `ui/theme`):

```
[ ⚗ AI Summary ]

  vLLM is not running.
  Enable AI feedback by starting the server:

  ┌──────────────────────────────────────────────┐
  │  pip install vllm                            │
  │  vllm serve Qwen/Qwen2.5-1.5B-Instruct \    │
  │    --max-model-len 4096                      │
  └──────────────────────────────────────────────┘

  Then set  enable_ai = true  in configs/default.toml
  and rerun the simulation.

  [ Retry Connection ]   [ Use Templates Only ]
```

Behaviour:
- **Retry Connection** button — re-runs health probe; if now reachable, triggers `generate_report()` and shows spinner then result
- **Use Templates Only** button (or `enable_ai = false` path) — displays template feedback strings from `metrics.json` directly without LLM, same Coach tab, labelled "Template feedback (AI offline)"
- Screen is a component embedded in `CoachScreen`, not a standalone screen; the "AI Summary" tab conditionally renders it
- When `enable_ai = false`, the "AI Summary" tab is hidden entirely (same behaviour as pre-Phase-4)

### Step 7 — Graceful error states (all paths)

| Situation | Behaviour |
| --- | --- |
| `enable_ai = false` | Tab hidden; zero network calls; no import of `ai/` |
| vLLM not running | Setup screen shown (Step 6); template feedback available |
| vLLM running, wrong model | Log warning with loaded model name; treat as offline for this session |
| vLLM timeout during generation | Show "AI summary unavailable — took too long"; template feedback shown |
| Malformed response / JSON error | Same as timeout; log details at DEBUG level |
| GPU OOM / vLLM crash mid-request | Connection error path; Retry button available |

No path should raise an unhandled exception to the UI event loop or the CLI caller.

### Step 8 — Tests

- `tests/test_ai_disabled.py` — no network call when `enable_ai = false`; `ai_report.md` not written
- `tests/test_ai_health.py` — `is_vllm_reachable()` returns `False` on connection refused (monkeypatched socket)
- `tests/test_ai_prompt.py` — prompt contains metrics JSON; system prompt contains "do not generate full solutions"; no engine class names leak into user prompt
- `tests/test_ai_mock.py` — mock HTTP returns fixed JSON; `ai_report.md` written with advisory header; scores in `metrics.json` unchanged after report generation
- `tests/test_ai_timeout.py` — mocked timeout → `complete()` returns `None`; no crash
- Mark live vLLM tests `@pytest.mark.integration` (skipped in CI unless `VLLM_AVAILABLE=1`)

## Out of scope

- Auto-fixing student code
- Cloud-only deployment requirement
- Replacing static analysis with LLM judgment
- Streaming responses in the UI (Phase 4 uses blocking calls; streaming is a future enhancement)
- Tournament batch AI (Phase 5 may call the same module per session)

## Definition of done

- [x] `enable_ai = false` runs with no AI dependency, no network calls, no `ai/` imports
- [x] `enable_ai = true` with vLLM running → `ai_report.md` written in session folder
- [x] `enable_ai = true` with vLLM offline → setup screen shown in Coach tab; template feedback displayed; no crash
- [x] Prompts include metrics only; system prompt forbids full solutions; checked by test string assertion
- [x] Scoring numbers in `metrics.json` unchanged after AI report generation
- [x] All error paths (offline, timeout, malformed response, OOM) return gracefully without exceptions
- [x] Retry button re-probes health and generates report if vLLM becomes available
- [x] `code-scenarios report --session` works on existing `metrics.json`
- [x] Documentation (README or Phase 4 verification block) lists recommended models and `vllm serve` commands
- [x] All unit tests pass; integration tests skipped unless `VLLM_AVAILABLE=1`

## Verification

```bash
# Unit tests (no vLLM needed)
pytest tests/test_ai_disabled.py tests/test_ai_health.py \
              tests/test_ai_prompt.py tests/test_ai_mock.py \
              tests/test_ai_timeout.py -v

# Smoke run with AI disabled (default)
code-scenarios run --scenario resource_wars \
    --bot student_bots/example_bot.py --seed 1
# Expect: no ai_report.md, no network activity

# With vLLM running (manual integration test):
#   vllm serve Qwen/Qwen2.5-1.5B-Instruct --max-model-len 4096
#   Set enable_ai = true in configs/default.toml
code-scenarios run --scenario resource_wars \
    --bot student_bots/example_bot.py --seed 1
# Expect: ai_report.md in session folder, advisory header present

code-scenarios report --session <latest_session_id>
# Expect: path to ai_report.md printed or "AI skipped" message

# Integration test suite (requires running vLLM)
VLLM_AVAILABLE=1 pytest -m integration -v
```

## References

- [PLAN.md §16 — Phase 4](../PLAN.md#16-development-phases)
- [PLAN.md §7 — AI Integration Strategy](../PLAN.md#7-ai-integration-strategy)
- [PLAN.md §9 — Configuration System](../PLAN.md#9-configuration-system)
- [PLAN.md §23 — Biggest Technical Risks](../PLAN.md#23-biggest-technical-risks)
- [vLLM documentation](https://docs.vllm.ai/en/latest/)
- [vLLM OpenAI-compatible server](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html)
