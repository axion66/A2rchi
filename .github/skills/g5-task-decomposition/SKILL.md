---
name: g5-task-decomposition
description: Guide for breaking complex features into manageable sub-tasks. Use when facing multi-component changes, large features requiring multiple specs, or planning parallel/sequential task execution.
---

# G5 Task Decomposition

This skill guides you through breaking complex features into manageable sub-tasks.

## When to Use This Skill

- Feature affects >3 specs
- Estimated work >1 week
- Multiple independent components
- Need to parallelize work
- Complex dependency graph

## When to Decompose

| Indicator | Action |
|-----------|--------|
| 1-3 affected specs | Single task |
| 4-7 affected specs | Consider decomposition |
| 8+ affected specs | Definitely decompose |
| Cross-cutting concerns | Decompose by concern |
| Team parallelization needed | Decompose for parallel work |

## Decomposition Process

### 1. Map the Dependency Graph

Identify which specs depend on which:

```
Component A (no deps) ─────────┐
                               │
Component B (no deps) ─────────┼──► Component D (deps: A, B, C)
                               │
Component C (deps: A) ─────────┘
```

### 2. Identify Natural Boundaries

Good boundaries:
- Independent subsystems
- Different layers (data, logic, UI)
- Different domains
- Clear interfaces between components

Bad boundaries:
- Splitting tightly coupled components
- Arbitrary file count splits
- Ignoring dependencies

### 3. Define Sub-Tasks

Each sub-task should:
- Have clear scope (what's in, what's out)
- Have testable deliverables
- Be independently mergeable
- Have defined dependencies on other sub-tasks

### 4. Order by Dependencies

Process sub-tasks in topological order:

```
Sub-task order:
1. WF-A (no deps) ─┐
2. WF-B (no deps) ─┼─► 4. WF-D (deps: A, B, C)
3. WF-C (dep: A) ──┘
```

## Example: Views System Decomposition

From [views-system.md](../../.g5/design_docs/views-system.md):

```
WF-0: Folder Restructure (no deps)
    │
    ├── WF-1: Input Context Mapping (dep: WF-0)
    ├── WF-2: View Spec Format (dep: WF-0)
    └── WF-3: View Instance Format (dep: WF-0)
            │
            └── WF-4: View Generator (deps: WF-1,2,3)
                    │
                    ├── WF-5: Sync Engine (dep: WF-4)
                    ├── WF-6: Reformat (dep: WF-4)
                    └── WF-7: Conflict Resolution (dep: WF-4)
                            │
                            └── WF-8: View Compiler (deps: WF-5,6,7)
                                    │
                                    └── WF-9: Prism Views Panel (dep: WF-8)
```

## Parallel vs Sequential

### Parallel Execution

Sub-tasks with no dependency between them can run in parallel:

```
Week 1: WF-0 (must complete first)
Week 2: WF-1, WF-2, WF-3 (parallel - no deps between them)
Week 3: WF-4 (depends on all Week 2 sub-tasks)
Week 4: WF-5, WF-6, WF-7 (parallel)
```

### Sequential Execution

When working alone or with shared state:

```
WF-1 → WF-2 → WF-3 → WF-4 → ...
```

## Sub-Task Definition Template

For each sub-task:

```markdown
### WF-{N}: {Name}

**Priority:** P{0-3}
**Dependencies:** {list of prerequisite sub-tasks}
**Scope:**
- {What's included}
- {What's included}

**Deliverables:**
- `path/to/spec.spec.md`
- `path/to/source.py`
- Tests for above

**Estimated effort:** {days/weeks}
```

## Spawn Commands

After decomposition, spawn sub-tasks:

```bash
# Start independent sub-tasks in parallel
g5 spawn wf-1-input-context-mapping
g5 spawn wf-2-view-spec-format
g5 spawn wf-3-view-instance-format

# After dependencies complete, start dependent sub-task
g5 spawn wf-4-view-generator
```

Or with `g5_newTask`:

```javascript
g5_newTask({ 
  name: "wf-1-input-context-mapping",
  description: "Input context mapping for views"
})
```

## Risk Assessment

For each sub-task, assess:

| Risk Factor | Questions |
|-------------|-----------|
| Technical complexity | New technology? Complex algorithms? |
| Dependencies | External services? Other sub-tasks? |
| Uncertainty | Clear requirements? Known approach? |
| Integration | How does it connect to other parts? |

```markdown
| Sub-Task | Risk | Mitigation |
|----------|------|------------|
| WF-1 (LSP) | High - LSP complexity | Start with markdown, defer code |
| WF-5 (Sync) | Medium - git merge | Start with source-wins |
```

## Common Mistakes

1. **Too granular** - Don't create a sub-task per file
2. **Ignoring dependencies** - Respect the dependency graph
3. **No clear boundaries** - Each sub-task needs defined scope
4. **Premature parallelization** - Start sequential, parallelize when needed
5. **Missing integration plan** - How do sub-tasks merge together?

## Integration Planning

Plan how sub-tasks come together:

```markdown
## Integration Points

1. WF-1,2,3 → WF-4: All format definitions used by generator
2. WF-5,6,7 → WF-8: Compiler uses sync/reformat/conflict
3. WF-8 → WF-9: UI triggers compiler operations

## Merge Strategy

- Feature branches per sub-task
- PR to main when sub-task complete
- Integration tests after each merge
```

## Checklist

Before decomposing:

- [ ] Identified all affected specs
- [ ] Mapped dependency graph
- [ ] Found natural boundaries
- [ ] Each sub-task has clear scope
- [ ] Dependencies between sub-tasks documented
- [ ] Parallel vs sequential decided
- [ ] Risk assessed for each sub-task
- [ ] Integration plan defined

> 💡 **Related skills**: 
> - [g5-design](../g5-design/SKILL.md) for design doc structure
> - [g5-workflow-guidance](../g5-workflow-guidance/SKILL.md) for managing tasks
