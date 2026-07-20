---
id: ISS-060
area: config
severity: med
status: fixed
---

# ISS-060: Dead Duplicated Knobs

## Symptom
max_turns unused; timeout defaults differ; duplicate denylists.

## Affected files
configs/default.toml; engine/core/config.py

## Fix sketch
Single source; wire or remove dead keys.
