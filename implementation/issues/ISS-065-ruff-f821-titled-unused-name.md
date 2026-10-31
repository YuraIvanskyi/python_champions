---
id: ISS-065
area: feedback
severity: med
status: fixed
---

# ISS-065: Undefined Name (F821) Shown As "Unused name"

## Symptom
`RUFF_PREFIXES` contains `F8`, so both F821 (undefined name -> NameError at runtime) and F841 (unused variable)
get the card title "Unused name" with the hint "Delete the name if you don't use it...". For a call to a nonexistent
function (typical typo) the hint is the opposite of what the student must do. Same in the uk catalog.

## Affected files
engine/i18n/feedback_strings.py (`RUFF_PREFIXES`, `feedback.ruff.F8.*`); engine/analysis/feedback.py (`_ruff_title`, `_ruff_fix_hint`)

## Fix sketch
Match full codes before prefixes: separate entries for F821 ("Undefined name": check spelling, define or import it)
and F841 ("Unused variable"). Keep F401 under the import card.

## Resolution
`RUFF_PREFIXES` now has full codes F811/F821/F822/F823/F841/F842 ahead of the F-family fallback, with en + uk titles and hints.
