---
id: ISS-064
area: feedback
severity: low
status: fixed
---

# ISS-064: BOT_DISPLAY_NAME / BOT_ICON_INDEX Reported As Unused Names

## Symptom
The custom AST pass collects every module-level assignment that is never read (`_assigned - _used`). The profile
constants from the starter template (`BOT_DISPLAY_NAME`, `BOT_ICON_INDEX`, `BOT_ICON`) are read by the loader, not by the
bot, so they are listed in `unused_names`. Effects: -3 `code_quality` points per name (max -15) and, with two or more
names, the "unused variables" style card. Verified: a bot with only these two constants and `make_turn` returns
`['BOT_DISPLAY_NAME', 'BOT_ICON_INDEX']`.

## Affected files
engine/analysis/static.py (`_AstAnalyzer.finalize_unused`); engine/scoring/code_quality.py; engine/analysis/feedback.py

## Fix sketch
Add the profile constants (and `get_bot_profile`) to the ignore set, or restrict the check to names assigned inside
functions. Add a test with the starter template.

## Resolution
`PROFILE_CONSTANTS` (`engine/core/bot_profile.py`) are skipped by the unused-name pass. Tests in `tests/test_coach_audit_fixes.py`.
