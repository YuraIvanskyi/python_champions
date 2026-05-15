# Implementation phases

Executable, step-by-step breakdown of the top-level [PLAN.md](../PLAN.md) for building the educational game framework. Each phase lives in its own `Phase_X.md` file with setup directives, implementation steps, and a clear done/not-done status.

## Quick start for agents

1. **Read** [PHASE_REGISTRY.yaml](PHASE_REGISTRY.yaml) — single source of truth for phase status.
2. **Pick** the lowest phase where `status` is `not_started` and every id in `depends_on` has `status: done`.
3. **Open** the matching `Phase_X.md` and follow it in order (Setup → Implementation steps → Verification).
4. **Before coding:** set that phase to `in_progress` in the registry, frontmatter, and `PHASE_STATUS` banner.
5. **After all Definition of done checkboxes pass and verification commands succeed:** set `status: done`, set `completed_at` (ISO date), update frontmatter and banner to `DONE`.
6. **If `status: done`:** skip re-implementation unless the user explicitly asks to redo or extend that phase.

Audit all phases quickly:

```bash
grep -r "PHASE_STATUS" implementation/
```

## Phase index

| ID | File | Title | Depends on | PLAN.md |
| --- | --- | --- | --- | --- |
| phase-0 | [Phase_0.md](Phase_0.md) | Project foundation | — | §5, §9, §20 |
| phase-1 | [Phase_1.md](Phase_1.md) | Minimal prototype | phase-0 | §16.1, §6, §10, §12–14 |
| phase-2 | [Phase_2.md](Phase_2.md) | Local GUI | phase-1 | §16.2, §11 |
| phase-3 | [Phase_3.md](Phase_3.md) | Analysis system | phase-1 | §16.3, §6.5, §15 |
| phase-4 | [Phase_4.md](Phase_4.md) | AI feedback | phase-3 | §16.4, §7 |
| phase-5 | [Phase_5.md](Phase_5.md) | Tournament mode | phase-2, phase-3 | §16.5, §13, §18 |
| phase-6 | [Phase_6.md](Phase_6.md) | Advanced scenarios | phase-5 | §16.6, §8.4 |

Current status is always authoritative in [PHASE_REGISTRY.yaml](PHASE_REGISTRY.yaml).

## MVP scope

**Phases 0–3** deliver the [Recommended First MVP](../PLAN.md#22-recommended-first-mvp): one grid scenario, student bot API, AI opponent, turn execution, simple replay, basic code analysis.

**Phases 4–6** are post-MVP: optional LLM feedback, classroom tournaments, and advanced scenario mechanics.

## Status convention (three layers)

Keep these in sync when changing status:

| Layer | Location | Values |
| --- | --- | --- |
| Registry | `PHASE_REGISTRY.yaml` → `status` | `not_started`, `in_progress`, `done` |
| Frontmatter | Top of each `Phase_X.md` → `status` | same |
| Banner | First line after frontmatter | `` `NOT_STARTED` ``, `` `IN_PROGRESS` ``, `` `DONE` `` |

**Rules**

- Never set `done` if any Definition of done checkbox is unchecked or verification commands fail.
- Set `in_progress` when starting work; set `done` and `completed_at` only after verification passes.
- Update **all three layers** in one commit when marking complete.

## PLAN.md reference map

| Topic | PLAN.md section |
| --- | --- |
| Architecture / folders | [§5 Proposed System Architecture](../PLAN.md#5-proposed-system-architecture) |
| Engine, loader, sandbox, scenarios | [§6 Core Modules](../PLAN.md#6-core-modules) |
| AI (later) | [§7 AI Integration Strategy](../PLAN.md#7-ai-integration-strategy) |
| Scenarios | [§8 Suggested Initial Scenarios](../PLAN.md#8-suggested-initial-scenarios) |
| Config | [§9 Configuration System](../PLAN.md#9-configuration-system) |
| Security | [§10 Security Strategy](../PLAN.md#10-security-strategy) |
| UI | [§11 UI/UX Strategy](../PLAN.md#11-uiux-strategy) |
| Data flow | [§12 Data Flow](../PLAN.md#12-data-flow) |
| Results / replay / scoring | [§13–15](../PLAN.md#13-result-system) |
| Development phases (source) | [§16 Development Phases](../PLAN.md#16-development-phases) |
| Bot API | [§17 Suggested Internal APIs](../PLAN.md#17-suggested-internal-apis) |
| Dependencies | [§20 Recommended Minimal Dependency Set](../PLAN.md#20-recommended-minimal-dependency-set) |
| MVP | [§22 Recommended First MVP](../PLAN.md#22-recommended-first-mvp) |
| Risks / success | [§23–24](../PLAN.md#23-biggest-technical-risks) |
