---
id: ISS-053
area: feedback
severity: med
status: fixed
---

# ISS-053: Ai Reports English Only

## Symptom
AI report generation hardcodes lang=en.

## Affected files
ai/prompts.py; engine/analysis/ai_report.py

## Fix sketch
Pass config locale to prompts.
