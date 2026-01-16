---
name: g5-hitl
description: Guide for human-in-the-loop decisions, escalation, and approval flows. Use when approval is needed, facing uncertain decisions, understanding HITL settings, or knowing when to escalate to humans.
---

# G5 Human-in-the-Loop (HITL)

This skill guides you through HITL decisions and approval flows.

## When to Use This Skill

- Phase transition needs approval
- Uncertain about a decision
- Need to understand HITL settings
- Want to know when to escalate
- Configuring approval rules

## What is HITL?

HITL = Human-in-the-Loop. A system where certain decisions require human approval before proceeding.

**Why HITL?**
- Catch errors before they propagate
- Human oversight on important changes
- Audit trail for decisions
- Safety net for agent operations

## HITL Settings File

Located at `src/g5/HITL_SETTINGS.yaml`:

```yaml
# HITL Settings for G5 Workflow

# Approval rules by operation type
approval_rules:
  new_spec:
    action: escalate  # Always ask human
    
  update_spec:
    action: auto_approve  # Agent can proceed
    conditions:
      - severity: minor
      - no_interface_change: true
    else: escalate
    
  code_only:
    action: auto_approve
    
  phase_transition:
    action: escalate  # Always ask human

# Escalation settings
escalation:
  notify: dashboard  # Show in Prism dashboard
  timeout: 3600      # 1 hour timeout
  default: block     # Block until resolved

# Features
features:
  enable_worktrees: false
```

## Approval Rules

### Action Types

| Action | Behavior |
|--------|----------|
| `auto_approve` | Agent proceeds without asking |
| `escalate` | Agent pauses, waits for human |
| `conditional` | Check conditions, then decide |

### Common Operations

| Operation | Default | Reason |
|-----------|---------|--------|
| `new_spec` | escalate | Creating new contracts is significant |
| `update_spec` | conditional | Minor updates auto-approve, major escalate |
| `code_only` | auto_approve | Implementation within existing spec |
| `phase_transition` | escalate | Human reviews phase completion |
| `delete_spec` | escalate | Removing contracts needs approval |

## Phase Transitions

All phase transitions require approval:

```javascript
// Agent calls this
g5_advancePhase({ 
  rationale: "Design doc complete with 5 specs identified" 
})

// System creates HITL decision
// Returns: { status: "pending_approval", decisionId: "hitl_123" }

// Human approves via dashboard or:
g5_approveHITL({ 
  decisionId: "hitl_123",
  rationale: "Looks good, proceed"
})

// Now agent can continue
```

## When to Escalate

**Always escalate when:**

1. 🚨 Spec and code contradict each other
2. 🚨 Creating a new spec (not in plan)
3. 🚨 Major interface changes
4. 🚨 Deleting or deprecating specs
5. 🚨 Uncertain about requirements
6. 🚨 External dependencies unclear
7. 🚨 Security-sensitive changes
8. 🚨 Breaking changes to public APIs

**Auto-approve when:**

1. ✅ Minor code fixes within existing signatures
2. ✅ Documentation updates
3. ✅ Test additions
4. ✅ Formatting/style changes
5. ✅ Bug fixes matching spec behavior

## Presenting Decisions

When escalating, provide clear context:

```markdown
🔔 **HITL Decision Required**

**Operation:** Update spec `auth/service.spec.md`

**What's changing:**
- Adding new method `refreshToken()`
- Modifying `login()` return type

**Why:**
- User requested refresh token support
- Return type change needed for new flow

**Impact:**
- Affects 3 downstream specs
- Requires code changes in `auth_service.py`

**Options:**
1. ✅ Approve - proceed with spec update
2. ❌ Reject - keep existing spec
3. 💬 Discuss - need more information

**Recommendation:** Approve (aligns with user request)
```

## HITL Decision Flow

```
Agent wants to do something
        │
        ▼
Check HITL_SETTINGS.yaml
        │
        ├── auto_approve? → Proceed immediately
        │
        └── escalate? → Create HITL decision
                │
                ▼
        Show in Prism dashboard
                │
                ▼
        Human reviews
                │
                ├── Approve → Agent continues
                │
                └── Reject → Agent stops, may revise
```

## Supervisor Mode

Agent has two modes:

### Worker Mode (default)
- Execute G5 phases
- Generate artifacts
- Make auto-approved decisions

### Supervisor Mode (triggered)
- Activated when HITL needed
- Minimal context usage
- Check approval rules
- Create/wait for HITL decisions

```python
# Conceptually:
if operation_needs_approval(action):
    switch_to_supervisor_mode()
    decision = create_hitl_decision(action, context)
    wait_for_approval(decision)
    switch_to_worker_mode()
    continue_execution()
```

## Approving Decisions

### Via Prism Dashboard
1. Open Prism sidebar
2. See pending decisions badge
3. Click to review
4. Approve or reject with rationale

### Via Tool
```javascript
g5_approveHITL({ 
  decisionId: "hitl_1768116978769_abc123",
  rationale: "Verified design matches requirements"
})
```

## Configuring HITL

### Make Everything Auto-Approve (Not Recommended)

```yaml
approval_rules:
  new_spec:
    action: auto_approve
  update_spec:
    action: auto_approve
  phase_transition:
    action: auto_approve
```

### Make Everything Escalate (Very Safe)

```yaml
approval_rules:
  new_spec:
    action: escalate
  update_spec:
    action: escalate
  code_only:
    action: escalate
  phase_transition:
    action: escalate
```

### Conditional Approval

```yaml
approval_rules:
  update_spec:
    action: conditional
    conditions:
      - change_type: documentation_only
      - change_type: test_only
    then: auto_approve
    else: escalate
```

## Common Mistakes

1. **Proceeding without approval** - Wait for HITL when required
2. **Vague escalation** - Provide clear context and options
3. **Not checking settings** - Know what needs approval
4. **Ignoring rejections** - Rejected means stop and revise
5. **Overusing escalation** - Trust auto-approve for minor changes

## HITL Checklist

When creating HITL decision:

- [ ] Clear description of action
- [ ] Context (what files, what changes)
- [ ] Impact assessment
- [ ] Options for human
- [ ] Recommendation if appropriate
- [ ] Decision ID tracked

> 💡 **Related skills**: 
> - [g5-workflow-guidance](../g5-workflow-guidance/SKILL.md) for phase transitions
> - [g5-spec-writing](../g5-spec-writing/SKILL.md) for spec change approvals
