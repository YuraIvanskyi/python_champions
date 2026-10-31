---
id: ISS-066
area: feedback
severity: med
status: fixed
---

# ISS-066: Plural Key Leaks Into Cards; Ukrainian Plural Wrong For Counts >= 5

## Symptom
0. `translate()` treats an empty catalog value as missing (`catalog.get(key) or en.get(key) or key`), so
   `translate("feedback.plural.empty")` returns the literal key. The stuck/oscillation cards then read
   "Your bot got stuck 1 timefeedback.plural.empty - ..." (en) and "Бот застряг 1 разfeedback.plural.empty - ..." (uk)
   whenever the count is exactly 1 (reproduced).
1. `feedback.plural.s` is "и" for any count above 1, so the uk card says "застряг 5 рази", "11 рази"; correct is
   "5 разів", "11 разів" ("2 рази" is right). Same for oscillation.
2. `translate()` returns the raw template if `str.format` raises `KeyError`/`ValueError`, so a missing keyword shows the
   student literal `{count}`, `{plural}`, `{range}` (reproduced: `translate("feedback.stuck.message", lang="uk", count=3)`).

## Affected files
engine/i18n/__init__.py (`translate`); engine/i18n/feedback_strings.py (`feedback.plural.*`); engine/analysis/feedback.py (stuck, oscillation)

## Fix sketch
Use `if key in catalog` instead of truthiness in `translate()` (an empty string is a valid translation). Replace the `plural` suffix by per-language plural helpers (uk: 1 / 2-4 / 5+, with 11-14 exceptions) or by
"раз(ів): N". Make `translate()` log and fall back to a safe format (`format_map` with defaults) instead of the raw template.

## Resolution
`translate()` uses `key in catalog`, fills missing placeholders with empty text (and logs) instead of returning the raw template; new `plural_suffix()` with uk one/few/many forms replaces `feedback.plural.s/empty`. The menu's `menu.bot_plural.*` strings (ui) were not touched.
