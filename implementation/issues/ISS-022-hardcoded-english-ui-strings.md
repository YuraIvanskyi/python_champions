---
id: ISS-022
area: style
severity: low
status: fixed
---

# ISS-022: Hardcoded English Ui Strings

## Symptom
English strings bypass i18n in scores/settings/ollama.

## Affected files
ui/screens/scores.py; settings.py

## Fix sketch
Move to ui_strings/feedback i18n.
