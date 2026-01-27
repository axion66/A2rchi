# Design: Authentication System

## Context

A2rchi needs proper authentication to support:
- User-specific preferences and BYOK keys (config-management proposal)
- Admin-only deployment settings
- Persistent identity across sessions

### Constraints
- Must work with existing PostgreSQL `users` table
- Flask-based application
- Support both interactive and non-interactive CLI setup
- Anonymous users should still work (no forced login)

### Stakeholders
- **Admins**: Manage deployment, designate other admins
- **Users**: Login, preferences, BYOK keys
- **Anonymous**: Can use chat, no persistence

## Goals / Non-Goals

### Goals
- GitHub SSO authentication
- Local account authentication (username/password)
- Admin role designation
- CLI setup wizard with non-interactive mode
- Session management with cookies
- Anonymous access preserved (full functionality, no persistence)

### Non-Goals
- Multiple SSO providers (future: Google, OIDC)
- MFA
- Role-based access beyond admin/user
- Separate API tokens (use same session auth)

## Key Decisions

### 1. Auth Library Stack

```
Authlib          → GitHub OAuth2 flow
Flask-Login      → Session management, @login_required
Werkzeug         → Password hashing (pbkdf2)
```

**Why not Flask-Security-Too?** Too heavy, we only need auth not the full security suite.

### 2. User Types

| Type | How Created | Capabilities |
|------|-------------|--------------|
| **Admin** | Setup wizard or `ADMIN_EMAIL` env | All settings, user management |
| **User** | Local signup or GitHub SSO | Own preferences, BYOK keys |
| **Anonymous** | Auto-created on first visit | Chat only, no persistence |

### 3. Anonymous Access (Mode C)

Anonymous users get full chat functionality but:
- No saved preferences
- No BYOK keys
- No conversation history persistence
- Session-only identity (lost on browser close)

```python
@app.before_request
def ensure_user():
    if not current_user.is_authenticated:
        # Create/load anonymous session user
        anon_id = session.get('anon_id') or str(uuid4())
        session['anon_id'] = anon_id
        g.user_id = f"anon:{anon_id}"
        g.is_anonymous = True
    else:
        g.user_id = current_user.id
        g.is_anonymous = False
```

### 4. CLI Setup Wizard

Interactive setup during `a2rchi init` or `a2rchi setup`:

```bash
$ a2rchi init --name mybot

=== A2rchi Setup ===

Admin Account Setup:
  Email: admin@example.com
  Password: ********
  Confirm: ********

GitHub OAuth (optional):
  Enable GitHub login? [y/N]: y
  Client ID: xxx
  Client Secret: xxx

✓ Admin account created
✓ GitHub OAuth configured
```

**Non-interactive mode:**
```bash
$ a2rchi init --name mybot --yes \
    --admin-email admin@example.com \
    --admin-password "$ADMIN_PASSWORD"
```

Or via environment variables:
```bash
export A2RCHI_ADMIN_EMAIL=admin@example.com
export A2RCHI_ADMIN_PASSWORD=secret
export GITHUB_CLIENT_ID=xxx
export GITHUB_CLIENT_SECRET=xxx

$ a2rchi init --name mybot --yes
```

### 5. Database Schema

Update `users` table:

```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS
    -- Auth fields
    password_hash VARCHAR(256),           -- For local accounts
    github_id VARCHAR(100),               -- GitHub user ID
    github_username VARCHAR(100),         -- GitHub username
    
    -- Role
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Session
    last_login_at TIMESTAMP,
    login_count INTEGER DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_users_github_id ON users(github_id) WHERE github_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_email_local ON users(email) WHERE password_hash IS NOT NULL;
```

### 6. Auth Flows

#### Local Login
```
POST /auth/login
  {email, password}
  → Verify password_hash
  → Create session
  → Set cookie
  → 200 {user}

POST /auth/logout
  → Clear session
  → Clear cookie
  → 200
```

#### Admin Creates User
```
POST /api/v2/admin/users  (admin only)
  {email, password, display_name, is_admin}
  → Hash password
  → Create user
  → 200 {user}
```

#### GitHub OAuth
```
GET /auth/github
  → Redirect to GitHub authorize URL

GET /auth/github/callback?code=xxx
  → Exchange code for token
  → Fetch GitHub user info (id, email, username)
  → Find user by github_id OR by email (auto-link)
  → If no user found, reject (admin must create account first)
  → Update github_id if linking by email
  → Create session
  → Redirect to app
```

### 7. Session Management

Using Flask-Login with server-side sessions in PostgreSQL:

```python
# Session storage in PostgreSQL
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(200) REFERENCES users(id),
    data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
```

**Session config:**
```python
app.config['SESSION_TYPE'] = 'postgresql'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

### 8. Admin Designation

Priority order:
1. `A2RCHI_ADMIN_EMAIL` env var → that user is admin
2. Setup wizard creates first admin
3. Existing admin can promote others via API

```python
def ensure_admin_exists():
    """Called on startup."""
    admin_email = os.environ.get('A2RCHI_ADMIN_EMAIL')
    if admin_email:
        user = get_or_create_user(email=admin_email)
        user.is_admin = True
        save_user(user)
```

### 9. Protected Endpoints

```python
from functools import wraps
from flask_login import current_user, login_required

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated

# Usage
@app.route('/api/v2/config/dynamic', methods=['PUT'])
@admin_required
def update_dynamic_config():
    ...

@app.route('/api/v2/user/preferences', methods=['PUT'])
@login_required
def update_preferences():
    ...

@app.route('/api/v2/chat', methods=['POST'])
def chat():
    # No decorator - anonymous allowed
    user_id = g.user_id  # Could be "anon:xxx" or real user
    ...
```

### 10. Static Config for Auth

```yaml
# In static_config
auth:
  session_lifetime_days: 30
  allow_registration: true      # Can new users sign up locally?
  github:
    enabled: true
    client_id: ${GITHUB_CLIENT_ID}
    # client_secret from secrets, not config
```

## File Structure

```
src/
├── auth/
│   ├── __init__.py
│   ├── service.py          # AuthService class
│   ├── models.py           # User model for Flask-Login
│   ├── decorators.py       # @login_required, @admin_required
│   ├── github.py           # GitHub OAuth flow
│   └── local.py            # Local auth (password)
├── interfaces/
│   └── chat_app/
│       └── auth_routes.py  # /auth/* endpoints
```

## Migration Plan

### Phase 1: Foundation
- [ ] Add auth columns to users table
- [ ] Create sessions table
- [ ] Implement AuthService
- [ ] Add Flask-Login integration

### Phase 2: Local Auth
- [ ] Implement registration endpoint
- [ ] Implement login/logout endpoints
- [ ] Password hashing with Werkzeug
- [ ] CLI setup wizard

### Phase 3: GitHub OAuth
- [ ] Authlib OAuth client setup
- [ ] GitHub auth flow endpoints
- [ ] User linking (GitHub → local account)

### Phase 4: Integration
- [ ] Add @login_required to protected endpoints
- [ ] Add @admin_required to admin endpoints
- [ ] Update CLI for non-interactive mode
- [ ] Update frontend for login UI

## API Endpoints

### Auth
```
POST /auth/login              # Local login
POST /auth/logout             # Logout (clear session)
GET  /auth/me                 # Current user info
GET  /auth/github             # Start GitHub OAuth
GET  /auth/github/callback    # GitHub OAuth callback
```

### Admin (requires @admin_required)
```
GET  /api/v2/admin/users      # List users
POST /api/v2/admin/users      # Create user (local account)
PUT  /api/v2/admin/users/:id  # Update user (e.g., make admin)
DELETE /api/v2/admin/users/:id # Delete user
```

## Resolved Decisions

| Question | Decision |
|----------|----------|
| First admin | Setup wizard + env var fallback |
| Anonymous access | Full functionality, no persistence |
| SSO providers | GitHub initially |
| Local accounts | Always available |
| API auth | Same as web (session cookies) |
| Registration | Admin-controlled (admin creates accounts) |
| Account linking | Auto-link GitHub to local account by email |

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Session storage in PostgreSQL adds load | Sessions are small, indexed by expiry for cleanup |
| GitHub OAuth requires internet | Local accounts always work as fallback |
| Cookie auth not ideal for CLI/scripts | Future: add API tokens |
| Anonymous users could abuse system | Rate limiting (future work) |

## Dependencies

Add to requirements:
```
authlib>=1.2.0
flask-login>=0.6.0
```
