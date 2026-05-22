---
phase_id: phase-3-1
status: done
depends_on: [phase-3, phase-2-8]
source_plan: PLAN.md §6.5, §11; coach screen
---

> **PHASE_STATUS:** `DONE`

# Phase 3.1 — Analysis gamification

## Goal

Add a **Code Coach** screen: scrollable bot source with line highlights, categorized quest cards (parchment/wood/stone panels), wired to `feedback_items` in `metrics.json` and Phase 2.8 skin.

## Prerequisites

- Phase 3 done (analysis pipeline, `metrics.json`)
- Phase 2.8 done (RPG skin)

## Implementation steps

1. `FeedbackItem` + `generate_feedback_items()` in `engine/analysis/feedback.py`
2. Embed `feedback_items` in `metrics.json`; keep string `feedback` for CLI
3. `bot_files` map in `replay.json` from `write_session`
4. `ui/screens/coach.py`, `code_panel.py`, `quest_card.py`, `scroll.py`
5. Scores screen **Code coach** navigation; `[ui.coach]` config
6. Tests: feedback items, metrics shape, coach data resolution

## Definition of done

- [x] `feedback_items` in analyzed sessions; CLI strings unchanged
- [x] Coach reachable from scores; highlights match Ruff/AST lines when available
- [x] Multi-bot per-player tabs work
- [x] Phase 3.1 tests pass; Phase 3 tests still pass

## Verification

```bash
python -m pytest tests/test_feedback_items.py tests/test_metrics_feedback_items.py tests/test_coach_data.py tests/test_feedback_templates.py -v
python -m code-scenarios run --scenario resource_wars --bot student_bots/example_bot.py --seed 1
python -m ui
```
