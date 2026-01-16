---
name: g5-design
description: Guide for creating design docs in Phase 1. Use when starting any new G5 task, capturing user intent, defining scope, or creating the initial design document.
---

# G5 Design Doc Creation

This skill guides you through creating design documents in Phase 1 of the G5 task lifecycle.

## When to Use This Skill

- Starting a new G5 task (`g5_newTask`)
- Need to capture user intent clearly
- Defining scope boundaries for a feature
- Creating the design doc at `.g5/design_docs/{feature-slug}.md`

## Why Design Docs Matter

The design doc is the **anchor** for your task:
- Prevents scope drift
- Captures what we ARE and ARE NOT building
- Defines success criteria (how we know we're done)
- Identifies affected specs (the plan)

**Without a design doc, you'll drift and build the wrong thing.**

## Design Doc Template

```markdown
# {Feature Name} Design Document

## Overview

{One paragraph explaining what we're building and why}

## Goals

1. {Primary goal}
2. {Secondary goal}
3. ...

## Non-Goals

- {What we're explicitly NOT doing}
- {Scope boundaries}

## Success Criteria

- [ ] {Measurable criterion 1}
- [ ] {Measurable criterion 2}
- [ ] {Criterion that can be checked off}

---

## Affected Specs

| Spec | Action | Reason |
|------|--------|--------|
| `path/to/spec.spec.md` | Create/Update | {Why} |

## Implementation Notes

{Technical approach, key decisions, alternatives considered}

## Open Questions

1. {Question that needs human input}
2. {Uncertainty to resolve}
```

## Step-by-Step Process

### 1. Parse the User Request

Extract from the user's message:
- **What** they want to build (the goal)
- **Why** they want it (the motivation)
- **Constraints** (timeline, tech choices, must-haves)
- **Context** (related systems, existing code)

### 2. Identify Task Type

| Type | Description | Example |
|------|-------------|---------|
| FEATURE | New capability | "Add user authentication" |
| BUGFIX | Fix broken behavior | "Login fails on Safari" |
| REFACTOR | Restructure without behavior change | "Split monolith into modules" |
| EXPLORATION | Research/spike | "Evaluate auth libraries" |

### 3. Write the Overview

One paragraph that answers:
- What are we building?
- Who is it for?
- What problem does it solve?

**Good**: "Implement a synchronized views system that aggregates content from specs and allows persona-specific editing with compile-to-workflow functionality."

**Bad**: "Add views feature." (too vague)

### 4. Define Goals and Non-Goals

**Goals** should be:
- Specific and measurable
- Ordered by priority
- Achievable in this task

**Non-Goals** are equally important:
- Explicitly scope out adjacent features
- Prevent scope creep
- Say "not in this task, maybe later"

### 5. Write Success Criteria

Each criterion should be:
- A checkbox (can be checked off)
- Objectively verifiable
- Specific enough to test

**Good**: "- [ ] Can define a view spec with sections, imports, and locks"

**Bad**: "- [ ] Views work well" (not specific)

### 6. Identify Affected Specs

List every spec that will need changes:

```markdown
| Spec | Action | Reason |
|------|--------|--------|
| `views/view_spec_format.spec.md` | Create | New spec for view templates |
| `state/state_schema.spec.md` | Update | Add views state keys |
```

This becomes your Phase 2 work plan.

### 7. Note Implementation Details

Capture technical decisions:
- Architecture choices
- Key algorithms
- Dependencies on other systems
- Risks and mitigations

### 8. List Open Questions

Things that need human input:
- Design trade-offs
- Unclear requirements
- External dependencies

## Design Doc Location

Always create at: `.g5/design_docs/{feature-slug}.md`

Naming convention:
- Lowercase
- Hyphens for spaces
- Descriptive but concise

Examples:
- `auth-refactor.md`
- `views-system.md`
- `g5-agent-skills.md`

## When is the Design Doc "Good Enough"?

Ready to advance when:
- [ ] Overview clearly states what we're building
- [ ] Goals are specific and prioritized
- [ ] Non-goals define scope boundaries
- [ ] Success criteria are checkboxes that can be verified
- [ ] Affected specs are identified
- [ ] No blocking open questions remain

## Common Mistakes

1. **Too vague** - "Make it better" → Be specific
2. **No non-goals** - Everything seems in scope → Define boundaries
3. **Unmeasurable success** - "Works well" → Use checkboxes
4. **Missing specs** - Forgetting affected areas → Think broadly
5. **Premature detail** - Implementation before design → Stay high-level

## Example: Good Design Doc

See [views-system.md](../../.g5/design_docs/views-system.md) for a complete example with:
- Clear overview
- Prioritized goals
- Explicit non-goals
- Verifiable success criteria
- Full spec breakdown
- Workflow decomposition

> 💡 **Related skills**: 
> - [g5-task-decomposition](../g5-task-decomposition/SKILL.md) for breaking down complex designs
> - [g5-workflow-guidance](../g5-workflow-guidance/SKILL.md) for advancing to Phase 2
