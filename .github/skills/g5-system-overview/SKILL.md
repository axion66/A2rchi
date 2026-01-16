---
name: g5-system-overview
description: High-level G5 architecture, key concepts, and file locations. Use this when new to G5, needing orientation, or understanding the overall system before diving into specific tasks.
---

# G5 System Overview

This skill provides orientation to the G5 (Design-Doc Driven Development) system.

## When to Use This Skill

- Starting a new session and unfamiliar with G5
- Need to understand where files live
- Want to know which skill to use for a specific task
- Debugging issues related to G5 workflow

## What is G5?

G5 = **Design-Doc Driven Development**. It's a 4-phase workflow that ensures:
- Specs are the source of truth
- Code matches specs exactly
- Changes are traceable and verified

## The 4-Phase Model

```
Phase 1: INTENT    → Capture what user wants, create design doc
Phase 2: SPEC      → Update specs with contracts and interfaces
Phase 3: CODE      → Implement code to match specs exactly
Phase 4: VERIFY    → Run tests, fix issues, complete task
```

| Phase | Name | Exit Criteria |
|-------|------|---------------|
| 1 | Intent | Design doc created, affected specs identified |
| 2 | Spec | All specs updated with contracts, test_file defined |
| 3 | Code | Code implements spec contracts |
| 4 | Verify | Tests pass, no errors, task complete |

## Key File Locations

```
src/g5/                    # G5 Framework (reusable, version controlled)
├── AGENT.md               # Agent instructions (READ THIS)
├── GATES.yaml             # Verification gates
├── INVARIANTS.yaml        # Global invariants
├── HITL_SETTINGS.yaml     # Human-in-the-loop config
├── specs/                 # Framework specs
├── mcp/                   # MCP server code
├── scripts/               # CLI tools
└── tests/                 # Framework tests

.g5/                       # Project State (ephemeral, gitignored)
├── state.sqlite           # Current task state
├── design_docs/           # Phase 1 output (design documents)
├── views/                 # Synchronized view instances
│   └── specs/             # View spec templates
├── specs/                 # Project-specific specs
└── experience/            # Lessons learned

src/prism/                 # VS Code Extension
├── specs/                 # Prism specs
└── src/                   # Extension source
```

## Key Concepts

### Specs
Markdown files (`.spec.md`) that define:
- Component interfaces (classes, methods, signatures)
- Contracts (preconditions, postconditions, errors)
- Testing requirements

### Contracts
Formal conditions that must be true:
- **PRE:** What must be true before calling
- **POST:** What will be true after
- **ERROR:** What errors can occur and when

### Views
Synchronized documents that aggregate content from specs:
- **View Spec**: Template defining view structure
- **View Instance**: Generated file with imported content
- Support readonly and editable sections

### HITL (Human-in-the-Loop)
Approval system for important decisions:
- Phase transitions require approval
- New specs may require approval
- Escalation for uncertain decisions

### Gates
Verification checkpoints at phase transitions:
- `INTENT_TO_SPEC` - Phase 1 → 2
- `SPEC_TO_CODE` - Phase 2 → 3
- `CODE_TO_VERIFY` - Phase 3 → 4
- `TASK_COMPLETE` - Final check

## MCP Tools (11 Total)

| Tool | Purpose |
|------|---------|
| `g5_getPhaseContext` | Load all context for current phase |
| `g5_getState` | Get current task state |
| `g5_updateStatus` | Update status/blockers |
| `g5_newTask` | Start new task |
| `g5_completeTask` | Complete task (Phase 4 only) |
| `g5_switchTask` | Switch between tasks |
| `g5_listTasks` | List available tasks |
| `g5_advancePhase` | Request phase transition |
| `g5_goBackPhase` | Navigate backward |
| `g5_checkGate` | Check specific gate |
| `g5_approveHITL` | Approve HITL decision |

## Which Skill Do I Need?

| Task | Skill |
|------|-------|
| Starting a new task | [g5-design](../g5-design/SKILL.md) |
| Writing a spec | [g5-spec-writing](../g5-spec-writing/SKILL.md) |
| Implementing code | [g5-codegen](../g5-codegen/SKILL.md) |
| Writing tests | [g5-testgen](../g5-testgen/SKILL.md) |
| Tests failing | [g5-debugging](../g5-debugging/SKILL.md) |
| Phase transitions | [g5-workflow-guidance](../g5-workflow-guidance/SKILL.md) |
| Need approval | [g5-hitl](../g5-hitl/SKILL.md) |
| Complex feature | [g5-task-decomposition](../g5-task-decomposition/SKILL.md) |
| Existing code, no specs | [g5-uplift](../g5-uplift/SKILL.md) |
| Prism UI work | [g5-prism-web-design](../g5-prism-web-design/SKILL.md) |
| Prism extension code | [g5-prism-extension](../g5-prism-extension/SKILL.md) |

## Common Mistakes

1. **Editing code without checking spec** - Always find the governing spec first
2. **Skipping design doc** - Phase 1 requires a design doc as anchor
3. **Reading state.sqlite directly** - Use `g5_getPhaseContext` instead
4. **Running tests on host** - Use Docker for consistent environment
5. **Ignoring gates** - Gates exist to catch issues early

## Quick Start

```bash
# 1. Check current state
g5_getPhaseContext

# 2. Read the design doc if in active task
cat .g5/design_docs/{feature}.md

# 3. Follow phase-appropriate skill
# Phase 1 → g5-design
# Phase 2 → g5-spec-writing
# Phase 3 → g5-codegen
# Phase 4 → g5-debugging
```

> 💡 **Related skills**: All skills reference back to this overview. Start here, then dive into specifics.
