---
name: g5-workflow-guidance
description: Guide for navigating G5 phases correctly. Use when making phase transition decisions, checking gates, deciding when to go backward, or understanding skip logic.
---

# G5 Workflow Guidance

This skill helps you navigate between G5 phases correctly.

## When to Use This Skill

- About to advance to the next phase
- Wondering if you should go back to an earlier phase
- Need to understand gate requirements
- Deciding whether to skip a phase

## Phase Reference Card

**MEMORIZE THIS:**

| # | Phase | Name | Exit Criteria |
|---|-------|------|---------------|
| 1 | INTENT | Intent + Plan | Design doc created, affected specs identified |
| 2 | SPEC | Spec Edits | All specs updated with contracts, test_file defined |
| 3 | CODE | Code Edits | Code implements spec contracts |
| 4 | VERIFY | Verify & Debug | Tests pass, no errors, task complete |

## Gate Checks

Before advancing, the system checks a gate:

| Gate | Transition | Key Checks |
|------|------------|------------|
| `INTENT_TO_SPEC` | 1 → 2 | Design doc exists, intent documented, affected specs listed |
| `SPEC_TO_CODE` | 2 → 3 | All specs have contracts, test_file defined in frontmatter |
| `CODE_TO_VERIFY` | 3 → 4 | Source files exist, code compiles |
| `TASK_COMPLETE` | Exit | All tests pass, no errors |

### Checking a Gate

```bash
# Check specific gate
g5_checkGate({ gateId: "SPEC_TO_CODE" })

# The tool returns pass/fail with details
```

## Advancing Phases

Use `g5_advancePhase` with a rationale:

```javascript
g5_advancePhase({ 
  rationale: "Design doc complete with 5 affected specs identified. All success criteria defined." 
})
```

**Important**: 
- Gate check runs automatically
- If gate fails, advance is refused
- If gate passes, HITL approval is required
- Human approves via Prism dashboard or `g5_approveHITL`

## Going Backward

Backward navigation is **trusted** - no HITL approval needed.

Use `g5_goBackPhase`:

```javascript
g5_goBackPhase({ 
  target_phase: 2, 
  reason: "Discovered spec is missing error handling contract" 
})
```

### When to Go Back

| Situation | Go Back To | Reason |
|-----------|------------|--------|
| Spec is wrong/incomplete | Phase 2 | Fix spec before continuing |
| Intent was misunderstood | Phase 1 | Revisit design doc |
| Missing a spec entirely | Phase 2 | Create the missing spec |
| Test reveals design flaw | Phase 2 | Update spec contracts |
| Just need code fix | Stay | No phase change needed |

### Decision Tree

```
Working in Phase N, discover issue:
│
├── Is the spec wrong?
│   └── YES → g5_goBackPhase(2, "spec issue")
│
├── Was intent misunderstood?
│   └── YES → g5_goBackPhase(1, "intent unclear")
│
├── Is it just a code bug?
│   └── YES → Stay in current phase, fix code
│
└── Is a spec missing entirely?
    └── YES → g5_goBackPhase(2, "missing spec")
```

## Skip Logic

Some phases can be skipped with justification:

| Phase | When to Skip |
|-------|--------------|
| Phase 2 (Spec) | No spec changes needed (pure documentation, config files) |
| Phase 3 (Code) | Spec-only change (updating contracts for existing code) |
| Phase 4 (Verify) | No testable code (documentation, design docs) |

### How to Skip

Advance with a rationale explaining the skip:

```javascript
g5_advancePhase({ 
  rationale: "Skipping Spec phase - skills are standalone markdown files, not governed by G5 specs" 
})
```

## Phase-Specific Guidance

### Phase 1: Intent
**Goal**: Capture what we're building

- Create design doc at `.g5/design_docs/{slug}.md`
- Define goals, non-goals, success criteria
- List affected specs
- Do NOT write specs or code yet

**Exit when**: Design doc is complete and reviewed

### Phase 2: Spec
**Goal**: Define contracts before code

- Create/update specs for all affected components
- Write preconditions, postconditions, error conditions
- Define `test_file` in frontmatter
- Process specs in dependency order (leaves first)

**Exit when**: All specs have complete contracts

### Phase 3: Code
**Goal**: Implement exactly what specs say

- Read spec's Structured Design Doc
- Match signatures exactly
- Implement guardrails
- Write tests as you go

**Exit when**: Code matches specs, tests written

### Phase 4: Verify
**Goal**: Ensure everything works

- Run full test suite (in Docker!)
- Fix failures (max 3 autofix attempts)
- Check spec-code sync
- Complete task

**Exit when**: All tests pass, `g5_completeTask` succeeds

## Common Mistakes

1. **Advancing without rationale** - Always explain why criteria are met
2. **Ignoring gate failures** - Fix the issue, don't bypass
3. **Going back unnecessarily** - Small code fixes don't need phase change
4. **Not going back when needed** - If spec is wrong, GO BACK
5. **Skipping without justification** - Document why skip is appropriate

## Status Updates

Use `g5_updateStatus` anytime to update progress:

```javascript
g5_updateStatus({ 
  status: "Implementing auth module, 3/5 specs done" 
})

// Add a blocker
g5_updateStatus({ 
  add_blocker: "Waiting for API key from admin" 
})

// Remove a blocker
g5_updateStatus({ 
  remove_blocker: "API key" 
})
```

## Task Completion

In Phase 4, after tests pass:

```javascript
g5_completeTask({ 
  summary: "Implemented 18 agent skills for G5 task system" 
})
```

This:
- Archives the task state
- Resets for next task
- Records experience (optional)

> 💡 **Related skills**: 
> - [g5-hitl](../g5-hitl/SKILL.md) for approval flows
> - [g5-debugging](../g5-debugging/SKILL.md) for Phase 4 issues
> - [g5-design](../g5-design/SKILL.md) for Phase 1 work
