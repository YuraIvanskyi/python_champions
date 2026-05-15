---
phase_id: phase-4
status: not_started
depends_on: [phase-3]
source_plan: PLAN.md §16 Phase 4, §7, §9, §23
---

> **PHASE_STATUS:** `NOT_STARTED`

# Phase 4 — AI feedback

## Goal

Add **optional local LLM integration** to generate readable summaries and teacher-friendly reports from existing metrics — without auto-fixing code or replacing grading ([PLAN.md §16.4](../PLAN.md#16-development-phases), [§7](../PLAN.md#7-ai-integration-strategy)).

## Prerequisites

- Phase 3 complete (`metrics.json` + feedback templates exist)
- Optional: [Ollama](https://ollama.com/) or other OpenAI-compatible endpoint available locally

## Setup

1. Extend `configs/default.toml`:

   ```toml
   [analysis]
   enable_ai = false

   [ai]
   provider = "ollama"
   base_url = "http://localhost:11434/v1"
   model = "phi4-mini"
   timeout_seconds = 30
   ```

2. Create `ai/` package:
   - `ai/client.py` — thin OpenAI-compatible HTTP client
   - `ai/prompts.py` — system/user prompt templates
   - `ai/__init__.py`

## Implementation steps

1. **AI client** in `ai/client.py`:
   - Read config from TOML
   - `complete(prompt: str) -> str` with timeout and connection error handling
   - No API keys in repo; document env var `OPENAI_API_KEY` if using cloud (optional, off by default)

2. **Prompt design** ([PLAN.md §7 AI Responsibilities](../PLAN.md#ai-responsibilities)):
   - Input: **only** structured metrics + feedback list + scenario name (no raw engine internals)
   - Output: short student summary + optional teacher paragraph
   - Explicit instructions in system prompt: do not generate full solutions, do not rewrite student code

3. **Report generator** in `engine/analysis/ai_report.py`:
   - If `enable_ai = false`, skip (zero cost path)
   - If true, call client after static/runtime analysis
   - Write `results/session_*/ai_report.md` (or `.txt`)

4. **Guardrails** ([PLAN.md §23.3](../PLAN.md#3-ai-hallucinations)):
   - AI text is labeled "advisory" in UI and reports
   - Final numeric grade always from Phase 3 scoring — never from LLM
   - On AI failure, fall back to template-only feedback

5. **CLI**:
   - `code-scenarios run ...` respects `enable_ai`
   - `code-scenarios report --session <id>` regenerates AI text from existing `metrics.json` without re-simulating

6. **UI integration** (if Phase 2 done):
   - Analysis panel tab: "AI summary" with disclaimer
   - Hide tab when `enable_ai = false`

7. **Supported models** — document in root README ([PLAN.md §7](../PLAN.md#recommended-local-models)):
   - Qwen 2.5 7B, Phi-4 Mini, Gemma 3 4B via Ollama

8. **Tests**:
   - `tests/test_ai_skipped_when_disabled.py` — no network call when `enable_ai = false`
   - `tests/test_ai_prompt.py` — prompt contains metrics JSON, forbids solution generation (string assert)
   - `tests/test_ai_mock.py` — mock HTTP client returns fixed text; report file written
   - Mark live Ollama tests `@pytest.mark.integration` (optional, manual)

## Out of scope

- Auto-fixing student code
- Cloud-only deployment requirement
- Replacing static analysis with LLM judgment
- Tournament batch AI (Phase 5 may call same module per session)

## Definition of done

- [ ] `enable_ai = false` runs with no AI dependency or network calls
- [ ] `enable_ai = true` produces `ai_report.md` in session folder when endpoint available
- [ ] Prompts include metrics only; system prompt enforces no full solutions
- [ ] Scoring numbers unchanged by AI layer
- [ ] Graceful fallback when Ollama offline
- [ ] `code-scenarios report --session` works on existing metrics
- [ ] Documentation lists recommended local models and setup
- [ ] Tests pass (mocked AI; integration optional)

## Verification

```bash
uv run pytest tests/test_ai_skipped_when_disabled.py tests/test_ai_prompt.py tests/test_ai_mock.py -v
uv run code-scenarios run --scenario resource_wars --bot student_bots/example_bot.py --seed 1
# With Ollama running and enable_ai = true:
uv run code-scenarios report --session <latest_session_id>
```

## References

- [PLAN.md §16 — Phase 4](../PLAN.md#16-development-phases)
- [PLAN.md §7 — AI Integration Strategy](../PLAN.md#7-ai-integration-strategy)
- [PLAN.md §9 — Configuration System](../PLAN.md#9-configuration-system)
- [PLAN.md §23 — Biggest Technical Risks](../PLAN.md#23-biggest-technical-risks)
