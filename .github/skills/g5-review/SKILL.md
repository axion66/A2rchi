---
name: g5-review
description: Guide for conducting phase-end reviews. Use at the end of every phase to verify work quality, check completeness, and ensure readiness for phase transition.
---

# G5 Phase Review

This skill guides you through conducting a review at the end of each phase.

## When to Use This Skill

- About to complete any phase
- Before calling `g5_advancePhase`
- When unsure if phase work is complete
- After significant changes within a phase
- Before requesting human approval

## Why Review at Phase End?

Reviews catch issues early:
- **Prevents gate failures** — catch missing requirements before the gate check
- **Reduces backward navigation** — find spec/design issues before coding
- **Improves quality** — systematic check ensures nothing is missed
- **Saves time** — fixing issues in-phase is cheaper than going back

## Phase 1 (INTENT) Review Checklist

Before advancing to Phase 2, verify:

### Design Doc Completeness
- [ ] Design doc exists at `.g5/design_docs/{feature_slug}.md`
- [ ] **Overview** section clearly describes what we're building
- [ ] **Goals** are specific and measurable
- [ ] **Non-goals** explicitly state what's out of scope
- [ ] **Success criteria** are defined and testable

### Scope Definition
- [ ] Affected specs are identified and listed
- [ ] Dependencies between specs are understood
- [ ] No ambiguous requirements remain
- [ ] Edge cases are considered

### Intent Clarity
- [ ] A new developer could understand the intent from the design doc alone
- [ ] No open questions that would block spec writing
- [ ] User's original request is fully addressed

### Review Command
```javascript
// Before advancing, check the gate
g5_checkGate({ gateId: "INTENT_TO_SPEC" })
```

## Phase 2 (SPEC) Review Checklist

Before advancing to Phase 3, verify:

### Spec Completeness
- [ ] All affected specs have been created/updated
- [ ] Each spec has YAML frontmatter with `test_file` defined
- [ ] Specs are in correct location (`.g5/specs/` or `.g5/meta/`)

### Contract Quality
- [ ] Each public function/method has a contract
- [ ] Contracts include:
  - [ ] **Preconditions** (what must be true before calling)
  - [ ] **Postconditions** (what will be true after)
  - [ ] **Invariants** (what never changes)
  - [ ] **Error conditions** (what can go wrong)

### Test Coverage Planning
- [ ] Test file path is realistic and follows project conventions
- [ ] Contracts are testable (not vague or unmeasurable)
- [ ] Edge cases from Phase 1 are covered in contracts

### Interface Stability
- [ ] Function signatures are finalized
- [ ] Data structures are fully defined
- [ ] No placeholder types or TODO comments in contracts

### Review Command
```javascript
// Before advancing, check the gate
g5_checkGate({ gateId: "SPEC_TO_CODE" })
```

## Phase 3 (CODE) Review Checklist

Before advancing to Phase 4, verify:

### Implementation Completeness
- [ ] All functions from specs are implemented
- [ ] Implementation matches spec signatures exactly
- [ ] All contracts are honored in the code

### Code Quality
- [ ] Code follows project style conventions
- [ ] No obvious bugs or logic errors
- [ ] Error handling matches spec error conditions
- [ ] No hardcoded values that should be configurable

### Test Readiness
- [ ] Test files exist at paths specified in specs
- [ ] Tests cover all contracts from specs
- [ ] Tests are runnable (imports work, fixtures exist)

### Spec-Code Sync
- [ ] Implementation file paths match spec expectations
- [ ] Function names match exactly
- [ ] Parameter types match spec definitions

### Review Command
```javascript
// Before advancing, check the gate
g5_checkGate({ gateId: "CODE_TO_VERIFY" })
```

## Phase 4 (VERIFY) Review Checklist

Before completing the workflow, verify:

### Test Results
- [ ] All tests pass (run in Docker for Python)
- [ ] No skipped tests without justification
- [ ] Test output is clean (no warnings that indicate issues)

### Integration
- [ ] Feature works end-to-end
- [ ] No regressions in existing functionality
- [ ] Error paths tested, not just happy path

### Documentation
- [ ] Code comments are adequate
- [ ] Any new public APIs are documented
- [ ] Design doc is still accurate (update if needed)

### Experience Capture
- [ ] Any learnings captured in `.g5/experience/`
- [ ] Tricky bugs documented for future reference
- [ ] Patterns worth remembering are recorded

### Review Command
```javascript
// Before completing, check the gate
g5_checkGate({ gateId: "WORKFLOW_COMPLETE" })
```

## Quick Review Protocol

For rapid reviews when confident:

```
1. Run gate check for current phase transition
2. Scan checklist headers (not every item)
3. Address any gate failures
4. Advance with clear rationale
```

## Deep Review Protocol

For complex features or after issues:

```
1. Read design doc/specs from scratch
2. Walk through every checklist item
3. Run relevant tests/commands
4. Document any concerns as blockers
5. Only advance when all checks pass
```

## Common Review Failures

### Phase 1 → 2
| Issue | Fix |
|-------|-----|
| No design doc | Create `.g5/design_docs/{slug}.md` |
| Vague scope | Add specific non-goals |
| Missing affected specs | List all specs that will change |

### Phase 2 → 3
| Issue | Fix |
|-------|-----|
| No `test_file` in frontmatter | Add to each spec YAML |
| Vague contracts | Make preconditions specific |
| Missing error conditions | Add error contracts |

### Phase 3 → 4
| Issue | Fix |
|-------|-----|
| Code doesn't compile | Fix syntax/import errors |
| Missing test files | Create test files at spec paths |
| Signature mismatch | Update code to match spec |

### Phase 4 → Complete
| Issue | Fix |
|-------|-----|
| Tests failing | Debug and fix (max 3 autofix attempts) |
| Flaky tests | Stabilize or document as known issue |
| Missing coverage | Add tests for uncovered contracts |

## Review Mindset

Ask yourself:
1. **Would I be embarrassed if a colleague reviewed this?**
2. **Can someone else pick up this work from where I left off?**
3. **Are there any "I'll fix this later" items that should be fixed now?**
4. **Does this actually solve the user's original problem?**

## After Review

If review passes:
```javascript
g5_advancePhase({ 
  rationale: "Phase X review complete: [specific evidence that criteria are met]" 
})
```

If review fails:
```javascript
// Add blocker and fix before advancing
g5_updateStatus({ 
  add_blocker: "Missing test_file in auth.spec.md frontmatter" 
})
```

## Related Skills

- [g5-workflow-guidance](../g5-workflow-guidance/SKILL.md) - Phase navigation rules
- [g5-design](../g5-design/SKILL.md) - Phase 1 design doc creation
- [g5-spec-writing](../g5-spec-writing/SKILL.md) - Phase 2 spec quality
- [g5-debugging](../g5-debugging/SKILL.md) - Phase 4 test failures
