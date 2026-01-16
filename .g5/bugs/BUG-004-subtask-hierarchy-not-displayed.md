# BUG-004: Subtask Hierarchy Not Displayed in Task List

## Summary
When a subtask is created with `g5_newTask` using `parent_branch`, the parent-child relationship is not visible in the G5 Prism task list or `g5_listTasks` output. Subtasks appear as sibling tasks at the same level as their parent.

## Symptoms
1. **G5 Prism panel shows flat list**: Both parent and subtask appear under "Not Started" at the same level
2. **`g5_listTasks` returns flat array**: No indication of parent-child relationship in the output
3. **No visual hierarchy**: Cannot distinguish parent tasks from subtasks

## Expected Behavior
- Subtasks should be visually nested under their parent task
- `g5_listTasks` should include `parent_task` or `parent_branch` field
- G5 Prism should show tree structure (parent → children)

Example expected output:
```
├── a2rchi-codebase-uplift (parent)
│   └── uplift-models-module (subtask)
```

## Actual Behavior
```
├── a2rchi-codebase-uplift
├── uplift-models-module
```
Both appear at same level with no relationship shown.

## Evidence

### g5_newTask response (correctly shows parent):
```json
{
  "status": "created",
  "task_id": "g5/uplift-models-module",
  "parent_branch": "g5/a2rchi-codebase-uplift",  // ← Parent IS tracked
  ...
}
```

### g5_listTasks response (missing parent info):
```json
{
  "tasks": [
    {
      "id": "g5/a2rchi-codebase-uplift",
      "name": "a2rchi-codebase-uplift",
      // No "children" or "subtasks" field
    },
    {
      "id": "g5/uplift-models-module",
      "name": "uplift-models-module",
      // No "parent_task" or "parent_branch" field
    }
  ]
}
```

### Git branch relationship (correct):
```
g5/uplift-models-module was created from g5/a2rchi-codebase-uplift
Both point to same commit: c18e377
```

## Root Cause
The `g5_listTasks` tool and G5 Prism tree view don't query or display the parent-child relationship that was established during `g5_newTask`. The relationship is:
1. Stored somewhere during creation (parent_branch is returned)
2. Not persisted in a way that `g5_listTasks` can retrieve
3. Not rendered in the UI

## Impact
- **Workflow confusion**: Can't see which tasks are subtasks
- **Task organization**: Flat list makes it hard to manage large projects with many subtasks
- **Context loss**: When switching tasks, unclear which is the parent orchestrating task

## Proposed Fixes

### Option A: Add parent_task field to g5_listTasks output
```json
{
  "id": "g5/uplift-models-module",
  "parent_task": "g5/a2rchi-codebase-uplift",  // Add this
  ...
}
```

### Option B: Add children array to parent tasks
```json
{
  "id": "g5/a2rchi-codebase-uplift",
  "children": ["g5/uplift-models-module"],  // Add this
  ...
}
```

### Option C: Tree structure in response
```json
{
  "tasks": [
    {
      "id": "g5/a2rchi-codebase-uplift",
      "subtasks": [
        { "id": "g5/uplift-models-module", ... }
      ]
    }
  ]
}
```

### Storage Options
1. Store parent_task in state.sqlite when creating subtask
2. Infer from git branch history (but fragile)
3. Store in a separate `.g5/tasks.json` manifest

## Related Bugs
- [BUG-001](BUG-001-new-task-branch-default.md): Branch creation default (fixed)
- [BUG-002](BUG-002-gitignore-state-files.md): Gitignore state files (fixed)
- [BUG-003](BUG-003-state-leaks-to-base-branch.md): State leaks on merge (open)

## Workaround
- Mentally track parent-child relationships
- Use naming convention (e.g., `uplift-models-module` implies child of `uplift-*` parent)
- Check git log to see branch origin

## Date Discovered
2026-01-16

## Status
OPEN - Needs MCP server enhancement
