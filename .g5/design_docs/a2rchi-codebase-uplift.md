# A2rchi Codebase Uplift

## Overview

Uplift the entire A2rchi codebase to G5 by extracting specs from existing code, module by module. This is a UPLIFT task - we're going from Code → Specs (reverse engineering).

## Goals

1. Extract specs from all major modules in the codebase
2. Document existing contracts, invariants, and APIs
3. Enable G5 workflow for future development
4. Improve code quality through spec-driven guardrails

## Non-Goals

- Refactoring existing code (this comes later)
- Adding new features
- Changing existing behavior
- Full test coverage (we document what exists)

## Success Criteria

- [ ] All major modules have specs extracted
- [ ] Specs accurately reflect current code behavior
- [ ] Existing tests are linked to specs
- [ ] G5 workflow can be used for future changes

## Module Inventory

Based on codebase analysis, here are the modules to uplift in priority order:

### High Priority (Core)

| Module | Path | Files | Description | Priority |
|--------|------|-------|-------------|----------|
| **Core A2rchi** | `src/a2rchi/a2rchi.py` | 1 | Main A2rchi class | HIGH |
| **Models** | `src/a2rchi/models/` | 12 | LLM model adapters (OpenAI, Anthropic, etc.) | HIGH |
| **Classic Pipelines** | `src/a2rchi/pipelines/classic_pipelines/` | 6 | QA, grading, chains | HIGH |
| **Utils** | `src/utils/` | 6 | Config loader, logging, SQL | HIGH |

### Medium Priority (Data & Storage)

| Module | Path | Files | Description | Priority |
|--------|------|-------|-------------|----------|
| **Data Manager** | `src/data_manager/data_manager.py` | 1 | Main data manager | MEDIUM |
| **Collectors - Base** | `src/data_manager/collectors/` | 4 | Base collectors, persistence | MEDIUM |
| **Collectors - Scrapers** | `src/data_manager/collectors/scrapers/` | 4+ | Web scrapers | MEDIUM |
| **Collectors - Tickets** | `src/data_manager/collectors/tickets/` | 3+ | Ticket systems | MEDIUM |
| **Vectorstore** | `src/data_manager/vectorstore/` | 3 | Vector DB manager | MEDIUM |
| **Retrievers** | `src/data_manager/vectorstore/retrievers/` | 5 | Retrieval strategies | MEDIUM |

### Medium Priority (CLI & Services)

| Module | Path | Files | Description | Priority |
|--------|------|-------|-------------|----------|
| **CLI Core** | `src/cli/` | 3 | CLI main, registries | MEDIUM |
| **CLI Managers** | `src/cli/managers/` | 5 | Config, deployment, secrets | MEDIUM |
| **Services (bin)** | `src/bin/` | 9 | Service entry points | MEDIUM |

### Lower Priority (Interfaces)

| Module | Path | Files | Description | Priority |
|--------|------|-------|-------------|----------|
| **Chat App** | `src/interfaces/chat_app/` | 4 | Flask chat interface | LOW |
| **Grader App** | `src/interfaces/grader_app/` | 1 | Grading interface | LOW |
| **Mattermost** | `src/interfaces/mattermost.py` | 1 | Mattermost integration | LOW |
| **Piazza** | `src/interfaces/piazza.py` | 1 | Piazza integration | LOW |
| **Redmine Mailer** | `src/interfaces/redmine_mailer_integration/` | 2+ | Redmine integration | LOW |

### Lower Priority (Advanced)

| Module | Path | Files | Description | Priority |
|--------|------|-------|-------------|----------|
| **Agents** | `src/a2rchi/pipelines/agents/` | 3+ | AI agents | LOW |
| **A2rchi Utils** | `src/a2rchi/utils/` | 2 | Output dataclass, VS connector | LOW |

## Subtask Breakdown

Each module will be a separate G5 subtask branched from this parent task:

### Batch 1: Core (Start Here)
1. **uplift-utils** - Utils module (`src/utils/`)
2. **uplift-models** - Models module (`src/a2rchi/models/`)
3. **uplift-core-a2rchi** - Core A2rchi class (`src/a2rchi/a2rchi.py`)
4. **uplift-classic-pipelines** - Classic pipelines (`src/a2rchi/pipelines/classic_pipelines/`)

### Batch 2: Data Layer
5. **uplift-collectors-base** - Collector base classes
6. **uplift-scrapers** - Web scrapers
7. **uplift-tickets** - Ticket collectors
8. **uplift-vectorstore** - Vectorstore and retrievers
9. **uplift-data-manager** - Data manager (depends on collectors/vectorstore)

### Batch 3: CLI & Services
10. **uplift-cli-core** - CLI core and registries
11. **uplift-cli-managers** - CLI managers
12. **uplift-services** - Service entry points

### Batch 4: Interfaces
13. **uplift-chat-app** - Chat web interface
14. **uplift-grader-app** - Grader interface
15. **uplift-integrations** - Mattermost, Piazza, Redmine

### Batch 5: Advanced
16. **uplift-agents** - AI agents
17. **uplift-a2rchi-utils** - A2rchi internal utils

## Dependency Graph

```
utils ────────────────────────────────────┐
                                          │
models ───────────────┐                   │
                      ▼                   ▼
            classic_pipelines ──► core_a2rchi
                      │
                      ▼
collectors_base ──► scrapers
              └──► tickets
                      │
vectorstore ◄─────────┘
     │
     ▼
data_manager
     │
     ▼
cli_core ──► cli_managers
     │
     ▼
services
     │
     ▼
interfaces (chat_app, grader_app, integrations)
     │
     ▼
agents
```

## Uplift Process Per Module

For each subtask:

1. **Phase 1 (Intent)**: Create design doc describing what module does
2. **Phase 2 (Spec)**: Extract spec from existing code
   - Read all source files
   - Identify classes, functions, public APIs
   - Document contracts (infer from code/tests)
   - Create `.g5/specs/{module}.spec.md`
3. **Phase 3 (Code)**: No code changes (uplift mode)
   - Verify spec matches existing code
   - Link existing test files
4. **Phase 4 (Verify)**: Run existing tests, mark spec as validated

## Risks

- **Incomplete test coverage**: Some modules may lack tests
- **Implicit contracts**: Behavior may not be documented
- **Tight coupling**: Some modules may be intertwined

## Timeline Estimate

- **Batch 1 (Core)**: 4 subtasks
- **Batch 2 (Data)**: 5 subtasks  
- **Batch 3 (CLI)**: 3 subtasks
- **Batch 4 (Interfaces)**: 3 subtasks
- **Batch 5 (Advanced)**: 2 subtasks

**Total: 17 subtasks**

## Next Steps

1. ✅ Create this parent uplift task
2. Create subtasks for Batch 1 (Core)
3. Begin with `uplift-utils` (fewest dependencies)
4. Work through dependency order
