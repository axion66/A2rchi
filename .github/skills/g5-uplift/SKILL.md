---
name: g5-uplift
description: Guide for onboarding existing code to G5 (reverse spec extraction). Use when working with a codebase that has no specs, extracting specs from existing code, or transitioning to G5 workflow.
---

# G5 Uplift

This skill guides you through onboarding existing code to G5.

## When to Use This Skill

- Codebase has no specs
- Want to adopt G5 for existing project
- Need to extract specs from code
- Transitioning from ad-hoc to spec-driven development

## What is Uplift?

**Normal G5**: Specs → Code (forward)
**Uplift G5**: Code → Specs (reverse)

Uplift extracts specs from existing code so you can use G5 going forward.

## Uplift Phases

| Phase | What Happens | Exit Criteria |
|-------|-------------|---------------|
| Survey | Scan codebase, inventory components | `survey.yaml` created |
| Triage | Set priority for each component | All components prioritized |
| Extract | Create specs from code | Spec file created |
| Validate | Run tests, verify spec matches | Tests pass |
| Reconcile | Mark as in-sync | Coverage threshold met |

## Getting Started

### 1. Initialize Uplift Mode

```bash
# Copy G5 framework to your repo
cp -r /path/to/src/g5 /your-repo/.g5

# Initialize uplift
cd /your-repo
./.g5/init.sh --uplift

# Or via CLI
python .g5/scripts/g5.py init --uplift
```

### 2. Survey the Codebase

```bash
python .g5/scripts/g5.py uplift survey
```

This creates `survey.yaml`:

```yaml
components:
  - path: src/auth/
    type: module
    files:
      - src/auth/service.py
      - src/auth/tokens.py
    estimated_size: medium
    
  - path: src/database/
    type: module
    files:
      - src/database/connection.py
      - src/database/models.py
    estimated_size: large
```

### 3. Triage Components

```bash
python .g5/scripts/g5.py uplift triage
```

Interactive prioritization:

```
Component: src/auth/
Files: 2 files, ~500 lines
Tests: tests/test_auth.py exists

Priority? (high/medium/low/skip): high
Reason: Core authentication, high change frequency

Component: src/database/
Files: 2 files, ~1200 lines
Tests: tests/test_database.py exists

Priority? (high/medium/low/skip): medium
Reason: Stable, rarely changes
```

### 4. Extract Specs

```bash
# Extract highest priority component
python .g5/scripts/g5.py uplift extract --next

# Or extract specific component
python .g5/scripts/g5.py uplift extract src/auth/
```

## Spec Extraction Process

### Agent-Driven Extraction

When you run `extract`, the agent:

1. **Reads all source files** in the component
2. **Identifies** classes, functions, public APIs
3. **Documents** what the code does
4. **Infers** contracts from behavior and tests
5. **Creates** spec stub

### Example Extraction

Source code:
```python
# src/auth/service.py
class AuthService:
    def __init__(self, db: Database):
        self.db = db
    
    def login(self, username: str, password: str) -> Token:
        user = self.db.find_user(username)
        if not user:
            raise UserNotFoundError(username)
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        return Token(user_id=user.id, expires=datetime.now() + timedelta(hours=24))
```

Extracted spec:
```markdown
---
component_id: auth/service
type: component
source_files:
  - src/auth/service.py
test_file: tests/test_auth.py
---

# AuthService

> ⚠️ **AUTO-GENERATED FROM CODE**: This spec was extracted from existing code.
> Review for accuracy and completeness.

## Overview

AuthService handles user authentication. It verifies credentials and issues JWT tokens.

## Structured Design Doc

### Classes

#### AuthService

Authentication service that validates credentials and issues tokens.

**Attributes:**
- `db: Database` - Database connection for user lookup

**Methods:**

##### `__init__(db: Database) -> None`

Initialize with database connection.

**Contracts:**
- PRE: `db` is valid Database instance
- POST: `self.db` is set

##### `login(username: str, password: str) -> Token`

Authenticate user and return token.

**Contracts:**
- PRE: `username` is not empty
- PRE: `password` is not empty
- POST: Returns Token with 24-hour expiration
- POST: Token contains correct user_id
- ERROR: `UserNotFoundError` when username not in database
- ERROR: `InvalidCredentialsError` when password wrong

## Guardrails

- Token expiration is always 24 hours
- Password is never stored in plain text

## Testing Contracts

- Login with valid credentials returns token
- Login with invalid username raises UserNotFoundError
- Login with wrong password raises InvalidCredentialsError
- Token contains correct user_id
- Token expires after 24 hours
```

### Review and Refine

After extraction:

1. **Review** the auto-generated spec
2. **Correct** any inaccuracies
3. **Add** missing contracts
4. **Remove** the auto-generated warning when verified

### 5. Validate

```bash
# Run tests to verify spec matches code
python .g5/scripts/g5.py uplift validate src/auth/
```

Validation checks:
- Tests pass
- Spec signatures match code
- Contracts are accurate

### 6. Check Progress

```bash
python .g5/scripts/g5.py uplift status
```

```
Uplift Progress:
  Total components: 47
  Surveyed: 47
  Triaged: 47
  Extracted: 12 (25%)
  Validated: 8 (17%)
  
High priority: 5/8 validated
Medium priority: 2/15 extracted
Low priority: 0/24 started
```

### 7. Exit Uplift Mode

When coverage threshold reached:

```bash
python .g5/scripts/g5.py uplift complete
```

This:
- Sets workflow mode to "normal"
- Marks all validated specs as in-sync
- Ready for standard G5 workflow

## Uplift State

In uplift mode, state.sqlite tracks:

```yaml
workflow:
  mode: "uplift"
  
uplift:
  phase: "extract"
  survey_complete: true
  components:
    - path: "src/auth/"
      status: "validated"
      priority: "high"
      spec_path: ".g5/specs/auth/service.spec.md"
    - path: "src/database/"
      status: "extracted"
      priority: "medium"
      spec_path: ".g5/specs/database/connection.spec.md"
```

## Coverage Thresholds

Default exit criteria:

```yaml
# 80% of high-priority components validated
coverage:
  high: 0.8
  medium: 0.5
  low: 0.0  # Not required
```

## Decision Tree

```
In Uplift Mode?
│
├── YES
│   ├── Phase = Survey? → Run uplift survey
│   ├── Phase = Triage? → Run uplift triage
│   ├── Phase = Extract? → Run uplift extract --next
│   ├── Phase = Validate? → Run tests, fix spec
│   └── Coverage met? → Run uplift complete
│
└── NO: Standard G5 workflow
```

## Common Mistakes

1. **Extracting everything** - Start with high-priority only
2. **Not reviewing specs** - Auto-generated specs need human review
3. **Skipping validation** - Tests must pass before moving on
4. **Wrong priority** - Prioritize by change frequency and risk
5. **Rushing** - Uplift is gradual, not all-at-once

## Uplift Checklist

- [ ] G5 framework copied to repo
- [ ] Uplift mode initialized
- [ ] Survey completed
- [ ] Components triaged
- [ ] High-priority components extracted
- [ ] Extracted specs reviewed
- [ ] Tests passing
- [ ] Coverage threshold met
- [ ] Uplift complete, normal mode

> 💡 **Related skills**: 
> - [g5-spec-writing](../g5-spec-writing/SKILL.md) for spec format
> - [g5-system-overview](../g5-system-overview/SKILL.md) for G5 basics
> - [g5-workflow-guidance](../g5-workflow-guidance/SKILL.md) for normal workflow
