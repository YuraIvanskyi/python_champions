---
phase_id: phase-2-9
status: done
depends_on: [phase-2-8]
source_plan: PLAN.md §11; user-requested launcher UX overhaul
completed_at: "2026-05-23"
---

> **PHASE_STATUS:** `DONE`

# Phase 2.9 — Launcher UX Overhaul

## Goal

Redesign the menu/launcher screen to make game mode selection, seed/map configuration, and opponent setup intuitive and visually polished. The current single-panel configuration mixes mutually exclusive workflows (single-bot-vs-AI and classroom match) into one form; this phase separates them cleanly and adds RPG-flavoured visual polish.

## Prerequisites

- Phase 2.8 done (RPG skin, procedural chrome, asset manifest)

## Current problems (from user feedback)

1. **Bot loading is confusing** — a single text field serves both "play my bot against AI" and "load all student bots for a classroom match", but these are mutually exclusive workflows.
2. **Seed selection is too granular** — the ±1 stepper is tedious; users want either a quick random seed or a recognisable map preset.
3. **Opponent mode is context-dependent** — it only applies when a single student bot plays against a built-in AI, yet it's always shown alongside multi-bot controls.
4. **Button text gets cut off** — `Browse…` and `Folder…` truncate on some layouts; `Rival (smart)` / `Rookie (practice)` also clip.
5. **Hotkey hints are duplicated** — the same hint string appears both inside the panel and in the footer.
6. **No explicit UI controls for hotkey actions** — scenario cycling and seed adjustment only work via keyboard; there are no visible arrow buttons.
7. **Buttons lack RPG iconography** — the reference skin has swords, shields, scrolls, etc.; current buttons are text-only.

---

## Design

### D1 — Two-mode launcher (radio/tab selection)

Replace the single right-panel configuration with a **mode selector** at the top of the right panel:

| Mode | Label | Description |
|------|-------|-------------|
| `practice` | **Practice (vs AI)** | One student bot plays against a built-in opponent (Rival or Rookie). |
| `classroom` | **Classroom Match** | 2–8 student bots compete on the same map; no built-in AI. |

Implementation: two `ListRow`-style tabs or radio buttons at the top of the right panel. Only one is active at a time. The rest of the panel content changes based on the active mode.

#### Practice mode panel contents

1. **Bot selector** — single file picker with Browse button (full-width, no truncation).
2. **Opponent picker** — Rival / Rookie radio with description and icon.
3. **Map / seed section** (see D2).
4. **Run Match** button.

#### Classroom mode panel contents

1. **Bots selector** — multi-file picker (Browse + Folder buttons) or a folder-drop area. Show count label: "4 bots loaded".
2. **Map / seed section** (see D2).
3. **Run Match** button.
4. Opponent picker is **hidden** (not applicable).

### D2 — Seed replaced with map picker + random option

Replace the `Stepper(seed)` widget with a two-option selector:

| Option | UI | Behavior |
|--------|-----|----------|
| **Random** | Toggle button labelled "Random (0–99)" | On click: pick `random.randint(0, 99)` at run time; display the chosen seed on the simulation HUD. |
| **Choose Map** | Grid of 4–5 minimap thumbnail buttons | Each thumbnail is a small (≈80×80 px) procedural preview rendered from a fixed seed. Clicking one selects that seed. |

Predefined map seeds (store in `configs/default.toml` under `[ui.map_presets]`):

| Preset | Seed | Flavour name |
|--------|------|--------------|
| 1 | 7 | "The Clearing" |
| 2 | 23 | "Obstacle Run" |
| 3 | 42 | "Classic" |
| 4 | 58 | "Open Field" |
| 5 | 91 | "The Maze" |

Each thumbnail is generated once at screen init by running `ResourceWarsScenario(seed=...).setup()`, reading the map grid, and rendering a tiny tile grid (≈10 px/tile) onto an 80×80 surface. Cache the surfaces.

### D3 — Opponent picker (practice mode only)

Move the opponent selector into its own clearly scoped sub-section visible **only** in Practice mode:

- Two large radio-style cards (≈ 240×60 each, stacked vertically or side-by-side).
- Each card shows: **icon** (rival.png / rookie.png at 32×32) + **name** + **one-line description**.
- Active card has a teal selection border; inactive is dimmed stone.
- No separate description label below — it's self-contained.

### D4 — Fix button truncation

- Increase `_BROWSE_W` and button widths so labels never exceed available text area.
- Audit every `Button` instantiation; ensure `rect.width >= font.size(label) + 2 * BUTTON_PAD_X + margin`.
- For opponent buttons: if two buttons don't fit side-by-side without truncation, stack them vertically or widen the panel.

### D5 — Promote hotkey actions to visible UI controls

Currently only keyboard shortcuts cycle scenarios and adjust seed. Add explicit clickable controls:

| Action | Current hotkey | New UI control |
|--------|---------------|----------------|
| Previous scenario | `↑` / `W` | **▲** button above scenario list (or left-arrow on the selected row) |
| Next scenario | `↓` / `S` | **▼** button below scenario list |
| Run match | `Enter` | Already exists as primary button |
| Quit | `Esc` | **✕ Quit** small button in the top-right corner or footer |

Move the hotkey hint text to a single compact line at the very bottom of the window (footer), not inside the configuration panel. Remove the duplicate hint inside the panel.

### D6 — RPG icons on buttons and menus

Add small (16–20 px) procedurally drawn or loaded icons inline with button labels:

| Element | Icon concept | Source |
|---------|-------------|--------|
| Run Match | ⚔ crossed swords | Procedural (two diagonal lines + guard) or `ui/assets/icons/run.png` |
| View Replays | 📜 scroll | Procedural (rounded rect with lines) or `ui/assets/icons/scroll.png` |
| Browse… | 📂 open folder | Procedural |
| Practice mode tab | 🛡 shield | Procedural or `ui/assets/icons/shield.png` |
| Classroom mode tab | 👥 two figures | Procedural or `ui/assets/icons/classroom.png` |
| Rival card | Uses existing `rival.png` | Already exists |
| Rookie card | Uses existing `rookie.png` | Already exists |
| Quit | ✕ or 🚪 door | Procedural |

Prefer procedural drawing first (like Phase 2.8 approach); fall back to PNG if procedural is too complex. Add an `draw_icon(surface, icon_name, rect)` helper in `ui/render/icons.py` or a new `ui/skin/menu_icons.py`.

---

## Implementation steps

### Setup

1. Confirm Phase 2.8 is `done` in `PHASE_REGISTRY.yaml`.
2. Set this phase to `in_progress` in registry, frontmatter, and banner.

### Step 1 — Mode selector widget

- Add a `ModeSelector` (or reuse two `ListRow` styled as tabs) at the top of the right panel.
- Wire `self.launch_mode` state (`"practice"` | `"classroom"`) into `MenuScreen`.
- Swap panel contents based on active mode; keep shared widgets (map/seed, Run Match) in both modes.

### Step 2 — Practice mode sub-panel

- Single bot path field + Browse button (full width, no Folder button in this mode).
- Opponent picker cards with icons (D3).
- Map/seed selector (D2 — can stub random-only first, add thumbnails in Step 4).
- Run Match button at bottom.
- Update `_start_run()` to enforce single-bot + opponent in practice mode.

### Step 3 — Classroom mode sub-panel

- Multi-bot path field + Browse + Folder buttons.
- Show loaded bot count label.
- Map/seed selector (shared with practice).
- Run Match button at bottom.
- Hide opponent picker entirely.
- Update `_start_run()` to enforce ≥2 bots and no opponent in classroom mode.

### Step 4 — Minimap thumbnail picker

- In `MenuScreen.__init__` or `on_enter`, generate 5 minimap preview surfaces from predefined seeds.
- Add `[ui.map_presets]` to `configs/default.toml` with seed → name mappings.
- Render a row/grid of clickable thumbnail widgets below the "Choose Map" / "Random" toggle.
- Selecting a thumbnail sets `self.seed` and highlights it; selecting "Random" deselects all thumbnails.

### Step 5 — Button width audit & truncation fix

- Calculate minimum widths for all buttons from their label text + padding.
- Adjust layout constants (`_BROWSE_W`, `_RW`, opponent button widths) so no label is ever truncated.
- If the right panel is too narrow, consider widening it (reduce left panel width or use full-width layout for some rows).

### Step 6 — Hotkey controls as UI buttons

- Add ▲/▼ arrow buttons flanking the scenario list (or above/below it).
- Add a small Quit button (top-right corner of the window, or in the footer bar).
- Consolidate hotkey hints into a single footer line; remove the duplicate inside the right panel.

### Step 7 — RPG menu icons

- Implement `draw_menu_icon(surface, name, rect)` with procedural fallback for: `swords`, `scroll`, `folder`, `shield`, `classroom`, `door`.
- Update `Button` widget to optionally accept an `icon` parameter; if present, draw icon to the left of the label text.
- Apply icons to: Run Match, View Replays, Browse, mode tabs, Quit.

### Step 8 — Polish and integration

- Ensure tab-key or click transitions between Practice/Classroom mode reset invalid state (e.g. clear opponent when switching to classroom).
- Verify that `_start_run` still correctly passes `opponent_mode` only in practice mode.
- Test window resizing (if supported) and default 1024×800 layout.
- Verify keyboard shortcuts still work alongside new buttons.

---

## Files likely modified

| File | Changes |
|------|---------|
| `ui/screens/menu.py` | Major rewrite — two-mode layout, minimap picker, icon buttons |
| `ui/widgets/controls.py` | `Button` icon support, possible `ModeSelector`/`RadioGroup` widget |
| `ui/render/icons.py` | New `draw_menu_icon()` procedural icon helper |
| `ui/skin/chrome.py` | Possible new `draw_radio_card()` helper |
| `ui/theme.py` | New layout constants if panel sizes change |
| `configs/default.toml` | `[ui.map_presets]` table |
| `engine/core/config.py` | `MapPreset` / preset loading in config model |

---

## Definition of done

- [ ] Mode selector (Practice / Classroom) works; switching modes shows/hides relevant controls
- [ ] Practice mode: single bot path + opponent picker (with icons) + map/seed selector
- [ ] Classroom mode: multi-bot path + bot count label + map/seed selector; opponent hidden
- [ ] Seed stepper replaced with Random toggle + 4–5 minimap thumbnail buttons
- [ ] Minimap thumbnails render correct procedural previews from predefined seeds
- [ ] No button label is truncated at default 1024×800 window size
- [ ] Scenario list has visible ▲/▼ navigation buttons
- [ ] Quit button exists as a clickable UI element
- [ ] Hotkey hints appear only in the footer (no duplicate inside panel)
- [ ] At least 4 RPG-style icons appear on buttons/tabs (Run, Replays, mode tabs)
- [ ] All existing keyboard shortcuts still work
- [ ] `_start_run()` correctly routes practice vs classroom match
- [ ] `uv run pytest -v` passes (no regressions)

## Verification

```bash
uv run python -m pytest tests/ -v
uv run python -m ui
# Manual: click Practice tab → pick bot → choose map thumbnail → Run Match
# Manual: click Classroom tab → Browse folder → Run Match
# Manual: verify no text is cut off on any button
# Manual: verify ▲/▼ and Quit buttons work
# Manual: verify icons render on Run Match, View Replays, mode tabs
```
