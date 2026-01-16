# BUG-002: .g5 state files incorrectly tracked in git

## Summary

The `.gitignore` had `.g5/` which should have excluded everything, but state files (`state.sqlite`, `activity.json`, `traces/`) were committed before the gitignore was added. Additionally, `.g5/` is too broad - we WANT to track design docs, specs, and bugs.

## Severity

**Medium** - Causes merge conflicts when switching tasks

## Root Cause

1. State files were committed before `.gitignore` was updated
2. Once tracked, `.gitignore` doesn't untrack files
3. `.g5/` in gitignore was too broad - excluded artifacts we want tracked

## Correct .gitignore Pattern

```gitignore
# G5 Workflow - ignore local state, keep artifacts
.g5/state.sqlite
.g5/activity.json
.g5/traces/
.g5/archive/
```

This ignores:
- `state.sqlite` - Local workflow state (per-machine)
- `activity.json` - Activity log (temporary)
- `traces/` - Debug traces (temporary)
- `archive/` - Archived task state (local)

This tracks (by not ignoring):
- `.g5/design_docs/` - Design documents (artifacts)
- `.g5/specs/` - Spec files (artifacts)
- `.g5/bugs/` - Bug reports (artifacts)
- `.g5/experience/` - Learnings (artifacts)
- `.g5/views/` - View instances (artifacts)
- `.g5/HITL_SETTINGS.yaml` - Config (should be tracked)

## Fix Applied

```bash
# Update .gitignore with correct patterns
# Then remove state files from tracking:
git rm --cached .g5/state.sqlite .g5/activity.json .g5/traces/unknown.jsonl
git commit -m "Fix .gitignore: track specs/design docs, ignore state files"
```

## Reported

- **Date**: 2026-01-16
- **Context**: Merge conflicts when completing uplift task
