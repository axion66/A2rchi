---
name: g5-experience-capture
description: Guide for documenting learnings in .g5/experience/. Use after bugs, discoveries, or patterns that should be remembered for future workflows.
---

# G5 Experience Capture

This skill guides you through documenting learnings for future reference.

## When to Use This Skill

- After fixing a tricky bug
- Discovering a non-obvious pattern
- Avoiding a repeated mistake
- Finding a workflow optimization
- Learning something that would help future sessions

## Why Capture Experience?

Experience files are:
- **Surfaced automatically** via `g5_getPhaseContext`
- **Tagged by phase** so relevant experience appears when needed
- **Persistent** across sessions and workflows
- **Searchable** for debugging similar issues

## Experience File Format

```yaml
# .g5/experience/2026-01-10-phase-transition-gotcha.md
---
date: 2026-01-10
title: Phase transition requires design doc
tags:
  - phase_transition
  - workflow
affects:
  - phase_transition
severity: important
---

# Phase Transition Requires Design Doc

## Problem

Tried to advance from Phase 1 to Phase 2 but gate failed with:
"Design doc not found"

## Root Cause

The `INTENT_TO_SPEC` gate requires a design doc at `.g5/design_docs/{slug}.md`.
Simply having intent in state.sqlite is not enough.

## Solution

Always create a design doc file in Phase 1:
```bash
# Create design doc
cat > .g5/design_docs/my-feature.md << 'EOF'
# My Feature

## Overview
...
EOF

# Update state to reference it
g5_updateStatus({ view_path: ".g5/design_docs/my-feature.md" })
```

## Prevention

- Check that design doc exists before advancing
- Use g5-design skill for Phase 1 work

## Related

- [g5-design](../.github/skills/g5-design/SKILL.md)
- [g5-workflow-guidance](../.github/skills/g5-workflow-guidance/SKILL.md)
```

## Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `date` | Yes | When this was learned |
| `title` | Yes | Brief description |
| `tags` | Yes | Categories for filtering |
| `affects` | Yes | When to surface this experience |
| `severity` | No | `critical`, `important`, `minor` |

## Tags Taxonomy

| Tag | Use When |
|-----|----------|
| `phase_transition` | About phase advancement/navigation |
| `spec_writing` | Creating or editing specs |
| `code_generation` | Implementing code from specs |
| `testing` | Writing or running tests |
| `sync_recovery` | Fixing spec-code divergence |
| `docker` | Docker-related issues |
| `hitl` | Approval/escalation issues |
| `prism` | VS Code extension issues |
| `views` | View system issues |

## Affects Values

Determines when experience is surfaced:

| Value | Surfaced During |
|-------|-----------------|
| `phase_transition` | Any phase change |
| `spec_writing` | Phase 2 (Spec) |
| `code_generation` | Phase 3 (Code) |
| `testing` | Phase 3-4 |
| `sync_recovery` | When sync issues detected |
| `all` | Always shown (use sparingly) |

## File Naming Convention

```
.g5/experience/
├── 2026-01-10-phase-transition-gotcha.md
├── 2026-01-11-docker-path-issue.md
├── 2026-01-12-spec-contract-pattern.md
└── 2026-01-12-testing-mock-pattern.md
```

Format: `{date}-{slug}.md`

## What to Capture

### Good Candidates

✅ Bug that took >30 minutes to find
✅ Non-obvious workaround
✅ Pattern that worked well
✅ Common mistake to avoid
✅ Tool usage discovery
✅ Configuration gotcha

### Not Good Candidates

❌ Obvious information (in docs)
❌ One-time issue (not repeatable)
❌ Personal preferences
❌ Temporary workarounds

## Experience Template

```markdown
---
date: {YYYY-MM-DD}
title: {Brief description}
tags:
  - {tag1}
  - {tag2}
affects:
  - {when_to_surface}
severity: {critical|important|minor}
---

# {Title}

## Problem

{What went wrong or was confusing}

## Root Cause

{Why it happened}

## Solution

{How to fix or work around it}

```code
{Code example if applicable}
```

## Prevention

{How to avoid this in the future}

## Related

- {Links to relevant skills or docs}
```

## How Experience is Surfaced

When you call `g5_getPhaseContext`, it includes:

```json
{
  "relevantExperience": [
    {
      "title": "Phase transition requires design doc",
      "file": ".g5/experience/2026-01-10-phase-transition-gotcha.md",
      "severity": "important"
    }
  ]
}
```

Experience is filtered by:
1. Current phase → matching `affects` values
2. Severity → `critical` always shown, others filtered

## Searching Experience

```bash
# Find all experience about testing
grep -l "testing" .g5/experience/*.md

# Find critical issues
grep -l "severity: critical" .g5/experience/*.md

# Search by content
grep -r "docker" .g5/experience/
```

## When to Write Experience

**Best times:**
- Just fixed a tricky bug → Document while fresh
- Discovered a pattern → Capture before forgetting
- Made a mistake → Document to prevent repeat

**Workflow:**
1. Solve the problem
2. Ask: "Would this help future sessions?"
3. If yes, write experience file
4. Keep it concise (1-2 minute read)

## Common Mistakes

1. **Too verbose** - Keep experiences short and actionable
2. **No code examples** - Include concrete examples
3. **Wrong tags** - Use standard taxonomy
4. **Not capturing** - If it took time to figure out, capture it!
5. **Duplicate info** - Check if already documented

## Example: Real Experience

```markdown
---
date: 2026-01-10
title: Docker volume mount requires absolute path
tags:
  - docker
  - testing
affects:
  - testing
severity: important
---

# Docker Volume Mount Requires Absolute Path

## Problem

Tests failing with "file not found" when running in Docker:
```
FileNotFoundError: /workspace/src/g5/tests/test_state_store.py
```

## Root Cause

Used relative path in volume mount:
```bash
docker run -v "./src":/workspace/src ...  # WRONG
```

Docker requires absolute paths for volume mounts.

## Solution

Use `$(pwd)` for absolute path:
```bash
docker run -v "$(pwd)/src":/workspace/src ...  # CORRECT
```

Or use the full project path:
```bash
docker run -v "/Users/me/project/src":/workspace/src ...
```

## Prevention

Always use `$(pwd)` in Docker volume mounts:
```bash
docker run --rm -v "$(pwd)":/workspace g5-runtime ...
```
```

> 💡 **Related skills**: 
> - [g5-debugging](../g5-debugging/SKILL.md) - often leads to experience capture
> - [g5-system-overview](../g5-system-overview/SKILL.md) - experience location
