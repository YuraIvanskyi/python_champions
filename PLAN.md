---
document: project-plan
purpose: Educational game framework — students write Python for turn-based scenarios
primary_audience: teachers, middle/high school students, programming clubs
implementation_language: Python 3.12+
section_count: 25
---

# Project Plan

> **Usage (LLM):** Read frontmatter and the Table of Contents first. Each numbered section (`## N. …`) is self-contained. Subsections use `###`. Preserve wording in body text; use section anchors when citing or updating a single area.

## Table of Contents

1. [Project Vision](#1-project-vision)
2. [Core Product Concept](#2-core-product-concept)
3. [Main Architectural Principles](#3-main-architectural-principles)
4. [Recommended Tech Stack](#4-recommended-tech-stack)
5. [Proposed System Architecture](#5-proposed-system-architecture)
6. [Core Modules](#6-core-modules)
7. [AI Integration Strategy](#7-ai-integration-strategy)
8. [Suggested Initial Scenarios](#8-suggested-initial-scenarios)
9. [Configuration System](#9-configuration-system)
10. [Security Strategy](#10-security-strategy)
11. [UI/UX Strategy](#11-uiux-strategy)
12. [Data Flow](#12-data-flow)
13. [Result System](#13-result-system)
14. [Replay System](#14-replay-system)
15. [Scoring System](#15-scoring-system)
16. [Development Phases](#16-development-phases)
17. [Suggested Internal APIs](#17-suggested-internal-apis)
18. [Teacher Workflow](#18-teacher-workflow)
19. [Student Workflow](#19-student-workflow)
20. [Recommended Minimal Dependency Set](#20-recommended-minimal-dependency-set)
21. [Future Expansion Possibilities](#21-future-expansion-possibilities)
22. [Recommended First MVP](#22-recommended-first-mvp)
23. [Biggest Technical Risks](#23-biggest-technical-risks)
24. [Success Criteria](#24-success-criteria)
25. [Final Recommendation](#25-final-recommendation)

---

## 1. Project Vision

### Goal

Create a lightweight, extensible educational game framework where students write Python code that participates in predefined game scenarios.

The system should:

- execute student-written Python code safely
- simulate turn-based game scenarios
- provide gameplay results
- analyze code quality and algorithms
- support local/offline classroom usage
- remain simple enough for incremental implementation

Primary audience:

- teachers
- middle/high school students
- programming clubs and competitions

## 2. Core Product Concept

### High-Level Workflow

```text
Teacher creates/selects scenario
        ↓
Students receive starter template
        ↓
Students implement allowed logic
        ↓
Students submit .py files
        ↓
Engine loads code dynamically
        ↓
Turn-based simulation executes
        ↓
Game metrics collected
        ↓
Static analysis executed
        ↓
Results + explanations displayed
```

## 3. Main Architectural Principles

### 3.1 Simplicity First

The system should:

- run locally
- avoid cloud dependencies
- avoid microservices
- avoid databases initially
- prefer plain files and JSON
- use pure Python as much as possible

### 3.2 Deterministic Simulations

All scenarios should:

- use seeded randomness
- support replayability
- allow debugging
- produce reproducible outcomes

### 3.3 Strong Separation

Separate:

- game engine
- scenario definitions
- student code
- analysis system
- UI layer

This prevents future rewrites.

## 4. Recommended Tech Stack

### Primary Stack

| Area | Technology | Reason |
| --- | --- | --- |
| Language | Python 3.12+ | Main execution language |
| UI | Pygame CE | Simplest graphical/game layer |
| Data Storage | JSON + filesystem | No DB complexity |
| Plugin Loading | importlib | Native dynamic loading |
| Static Analysis | Ruff + Radon + AST | Lightweight and powerful |
| Sandboxing | subprocess + timeouts | Minimal viable isolation |
| Packaging | uv or pip | Simple dependency management |
| Config | TOML | Human-readable |
| Testing | pytest | Standard ecosystem |
| AI Integration | Ollama/OpenAI-compatible API | Optional local analysis |

### Why Pygame CE

Advantages:

- beginner friendly
- minimal setup
- easy rendering
- turn-based logic is trivial
- large educational ecosystem
- works offline
- good for 2D grids/maps

Avoid:

- Unity
- Godot
- web stack
- Electron
- heavy engines

They increase complexity significantly.

## 5. Proposed System Architecture

```text
project/
│
├── engine/
│   ├── core/
│   ├── simulation/
│   ├── sandbox/
│   ├── scoring/
│   └── analysis/
│
├── scenarios/
│   ├── resource_wars/
│   ├── maze_runner/
│   └── team_battle/
│
├── student_bots/
│
├── ai/
│
├── ui/
│
├── configs/
│
├── results/
│
└── tests/
```

## 6. Core Modules

### 6.1 Engine Core

Responsible for:

- turn execution
- entity management
- game loop
- state updates
- action validation

Core abstractions:

- Game
- Scenario
- Player
- Bot
- Map
- Entity
- Action
- TurnResult

### 6.2 Student Code Loader

Loads user code dynamically.

Preferred approach:

- each student submits one Python file
- file contains predefined function/class

Example:

```python
def make_turn(game_state):
    return "MOVE_RIGHT"
```

Alternative advanced API:

```python
class StudentBot(BotBase):
    def make_turn(self, state):
        ...
```

### 6.3 Sandbox Layer

Purpose:

- prevent crashes
- prevent infinite loops
- isolate runtime

Minimal viable solution:

- execute in subprocess
- strict timeout
- memory limits where possible
- restricted imports
- no filesystem/network access

Initially acceptable:

- soft sandboxing only

Later:

- container isolation

### 6.4 Scenario System

Each scenario defines:

- map
- rules
- victory conditions
- allowed actions
- scoring logic

Scenario interface:

```python
class ScenarioBase:
    def setup(self):
        ...

    def apply_turn(self):
        ...

    def calculate_score(self):
        ...
```

### 6.5 Analysis Engine

#### Static Analysis

Use:

- ast
- ruff
- radon

Metrics:

- syntax errors
- linting
- cyclomatic complexity
- nesting depth
- unused variables
- function lengths
- forbidden constructs

#### Runtime Analysis

Metrics:

- execution time
- crashes
- invalid actions
- timeout count
- stability

#### Educational Feedback Layer

Translate technical metrics into:

- student-friendly explanations
- recommendations
- learning hints

Example:

> Your code works correctly, but contains very complex conditions.
> Try splitting logic into smaller functions.

## 7. AI Integration Strategy

### Purpose

AI should:

- explain errors
- summarize strengths/weaknesses
- generate readable feedback
- avoid replacing learning

### Recommended Local Models

#### Small Local Models

| Model | Usage |
| --- | --- |
| Qwen 2.5 7B Instruct | General analysis |
| Phi-4 Mini | Fast classroom usage |
| Gemma 3 4B | Lightweight feedback |

Use through:

- Ollama
- OpenAI-compatible APIs

### AI Responsibilities

Allowed:

- explain complexity
- summarize mistakes
- compare strategies
- generate teacher comments

Avoid:

- auto-fixing student code
- generating full solutions

## 8. Suggested Initial Scenarios

### 8.1 Resource Wars

Grid map:

- gather resources
- avoid enemies
- maximize score

Concepts:

- loops
- pathfinding
- conditions

### 8.2 Maze Runner

Bot navigates maze.

Concepts:

- algorithms
- state tracking
- optimization

### 8.3 Survival Arena

Bots survive longest.

Concepts:

- strategy
- risk analysis
- resource management

### 8.4 Team Capture

Multiple bots cooperate.

Concepts:

- communication APIs
- modular design
- teamwork

## 9. Configuration System

Use TOML.

Example:

```toml
[engine]
turn_timeout_ms = 100
max_turns = 300

[analysis]
enable_ai = true
enable_static_analysis = true
```

## 10. Security Strategy

### Initial Stage

Acceptable protections:

- subprocess execution
- import restrictions
- timeout kills
- execution quotas

### Later Stages

Add:

- Docker isolation
- syscall restrictions
- filesystem virtualization

## 11. UI/UX Strategy

### MVP Interface

Simple desktop application:

- scenario selection
- player loading
- simulation viewer
- scoreboard
- analysis panel

### Visualization Style

Prefer:

- simple 2D tile maps
- pixel/grid aesthetic
- deterministic animations

Avoid:

- real-time physics
- complex rendering
- multiplayer networking

## 12. Data Flow

```text
Scenario selected
      ↓
Student bots loaded
      ↓
Validation phase
      ↓
Simulation begins
      ↓
Turns executed
      ↓
Metrics collected
      ↓
Analysis generated
      ↓
Results exported
```

## 13. Result System

Each execution produces:

```text
results/
    session_001/
        replay.json
        metrics.json
        logs.txt
        screenshots/
```

## 14. Replay System

Store:

- random seed
- turns
- actions
- map states

Allows:

- debugging
- tournament playback
- classroom demonstrations

## 15. Scoring System

### Gameplay Score

Examples:

- resources gathered
- survival time
- objectives completed

### Code Quality Score

Examples:

- low complexity
- readability
- low error count
- performance

### Combined Formula

```text
final_score =
    gameplay_score * 0.7 +
    code_quality * 0.3
```

Configurable per scenario.

## 16. Development Phases

### Phase 1 — Minimal Prototype

Goal:
single-player turn simulation.

Implement:

- basic engine
- one scenario
- dynamic bot loading
- terminal output
- turn system

No GUI yet.

### Phase 2 — Local GUI

Implement:

- Pygame rendering
- visual map
- replay viewer
- score screen

### Phase 3 — Analysis System

Implement:

- Ruff integration
- Radon metrics
- AST analysis
- execution metrics

### Phase 4 — AI Feedback

Implement:

- local LLM integration
- readable summaries
- teacher-friendly reports

### Phase 5 — Tournament Mode

Implement:

- multiple students
- batch execution
- rankings
- replay browser

### Phase 6 — Advanced Scenarios

Implement:

- teams
- shared resources
- fog of war
- communication APIs

## 17. Suggested Internal APIs

### Bot API

```python
class BotBase:
    def make_turn(self, game_state):
        pass
```

### Game State

Provide readonly simplified data:

```json
{
    "position": [4, 2],
    "resources": 10,
    "visible_tiles": [...]
}
```

Never expose engine internals.

## 18. Teacher Workflow

```text
Select scenario
    ↓
Distribute starter template
    ↓
Collect submissions
    ↓
Run tournament
    ↓
Display results
    ↓
Review analysis
```

## 19. Student Workflow

```text
Open local practice environment
    ↓
Edit bot logic
    ↓
Test against AI bots
    ↓
Improve strategy
    ↓
Submit file
```

## 20. Recommended Minimal Dependency Set

- pygame-ce
- pytest
- ruff
- radon
- tomli
- pydantic

Optional:

- rich
- numpy

Avoid initially:

- fastapi
- django
- react
- postgres
- redis
- kubernetes

## 21. Future Expansion Possibilities

### Web Version

Possible future:

- FastAPI backend
- browser visualization
- remote tournaments

Not recommended initially.

### Multiplayer Networking

Possible later:

- LAN classroom tournaments
- teacher host mode

### Curriculum Analytics

Possible:

- skill progression
- concept mastery
- learning statistics

## 22. Recommended First MVP

Implement ONLY:

### Features

- one grid scenario
- one student bot API
- one AI opponent
- turn execution
- simple replay
- basic code analysis

### Technical Stack

- Python
- Pygame CE
- Ruff
- Radon

### Time Estimate

2–4 weeks for stable MVP

## 23. Biggest Technical Risks

### 1. Safe Code Execution

Mitigation:

- subprocess isolation
- strict APIs
- no unrestricted imports

### 2. Overengineering

Mitigation:

- keep scenarios simple
- avoid networking
- avoid databases initially

### 3. AI Hallucinations

Mitigation:

- AI only explains metrics
- never trusted for grading

## 24. Success Criteria

The project succeeds if:

- students can write simple Python logic
- scenarios are easy to create
- tournaments are reproducible
- teachers can launch sessions quickly
- analysis is understandable for beginners
- local execution works reliably without internet

## 25. Final Recommendation

The optimal initial implementation is:

- pure Python
- local desktop application
- Pygame CE visualization
- subprocess-based sandboxing
- JSON/TOML storage
- static analysis via Ruff/Radon/AST
- optional local LLM integration via Ollama

This provides:

- low complexity
- educational accessibility
- easy deployment
- offline compatibility
