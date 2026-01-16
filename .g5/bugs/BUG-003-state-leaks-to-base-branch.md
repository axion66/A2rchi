# BUG-003: Task State Leaks to Base Branch After Merge

## Summary
When a subtask branch is merged to the base branch (`jason-g5`), the `.g5/state.sqlite` from the subtask pollutes the base branch state. The base branch now shows the subtask's name, phase, and status instead of its own identity.

## Symptoms
1. **G5 Prism panel shows wrong task**: "uplift-core-a2rchi" appears as "In Progress" even though we're on `jason-g5` branch
2. **`g5_listTasks` shows confused state**: 
   - `jason-g5` branch shows `name: "Uplift Core A2rchi"` and `phase: 4`
   - The actual subtask branch `g5/uplift-core-a2rchi` shows `phase: null` (no state readable)
3. **Task identity is wrong**: The base branch should have its own task identity (the parent "A2rchi G5 Uplift" task), not inherit from merged subtasks

## Expected Behavior
- `jason-g5` should retain its own task identity as the parent "A2rchi G5 Uplift" task
- Completed subtasks should either:
  - Be marked as "Completed" in the task list, OR
  - Have their state cleaned up after merge

## Actual Behavior
- `jason-g5` inherited the state from `g5/uplift-core-a2rchi` when that branch was merged
- The `.g5/state.sqlite` from the subtask overwrote the parent task's state

## Root Cause
The `.g5/state.sqlite` file is committed to git (per our decision to track artifacts). When we merge a subtask branch:
```
git checkout jason-g5
git merge g5/uplift-core-a2rchi
```
The subtask's `state.sqlite` gets merged in, overwriting the parent branch's state.

## Evidence
```
Current branch: jason-g5
g5_getPhaseContext shows:
  - name: "Uplift Core A2rchi"  (should be parent task name)
  - phase: 4 (Verify)
  - status: "Design doc and spec created for core A2rchi class"

g5_listTasks shows jason-g5 as:
  - name: "Uplift Core A2rchi" 
  - phase: 4
  - isActive: true
```

## Impact
- **Workflow confusion**: Can't tell what task we're actually on
- **Parent task lost**: The parent "A2rchi G5 Uplift" task state is gone
- **Subtask completion broken**: No way to mark subtasks as "Completed" in the list

## Proposed Fixes

### Option A: Ignore state.sqlite in git (RECOMMENDED)
Add to `.gitignore`:
```
.g5/state.sqlite
```
- Each branch maintains its own local state
- Merges only bring artifacts (specs, design docs)
- Cleaner separation of concerns

### Option B: Branch-aware state
- Store task state keyed by branch name in the database
- Each branch reads/writes only its own state
- More complex but preserves full history

### Option C: Post-merge state reset
- After merging subtask, automatically reset parent branch state
- Requires manual or hook-based cleanup
- Error-prone

## Related Bugs
- [BUG-001](BUG-001-new-task-branch-default.md): Branch creation default (fixed)
- [BUG-002](BUG-002-gitignore-state-files.md): Gitignore state files (partially addressed this)

## Workaround
Until fixed, after merging a subtask:
1. Delete the subtask state: `rm .g5/state.sqlite`
2. Create a new task with `g5_newTask` to reset state
3. Or manually restore parent task state

## Date Discovered
2026-01-16

## Status
OPEN - Needs MCP server fix or workflow change
