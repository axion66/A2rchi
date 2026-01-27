# Spec: Authentication Service

## Overview
Provides user authentication via local accounts and GitHub OAuth, with session management stored in PostgreSQL.

---

## ADDED Requirements

### Requirement: User Authentication
The system SHALL authenticate users via local accounts (email/password) or GitHub OAuth.

#### Scenario: Local login with valid credentials
- **GIVEN** a user with email "user@example.com" exists with a password hash
- **WHEN** POST /auth/login with {email: "user@example.com", password: "correct"}
- **THEN** password is verified against hash
- **AND** a session is created in the sessions table
- **AND** a session cookie is set
- **AND** response is 200 with user info

#### Scenario: Local login with invalid credentials
- **GIVEN** a user with email "user@example.com" exists
- **WHEN** POST /auth/login with {email: "user@example.com", password: "wrong"}
- **THEN** response is 401 with {error: "Invalid credentials"}
- **AND** no session is created

#### Scenario: Login with non-existent user
- **WHEN** POST /auth/login with {email: "nobody@example.com", password: "any"}
- **THEN** response is 401 with {error: "Invalid credentials"}

#### Scenario: Logout
- **GIVEN** a user is logged in with a valid session
- **WHEN** POST /auth/logout
- **THEN** the session is deleted from sessions table
- **AND** the session cookie is cleared
- **AND** response is 200

---

### Requirement: GitHub OAuth Authentication
The system SHALL support authentication via GitHub OAuth2.

#### Scenario: Initiate GitHub login
- **WHEN** GET /auth/github
- **THEN** user is redirected to GitHub authorization URL
- **AND** state parameter is stored in session for CSRF protection

#### Scenario: GitHub callback with existing user (by github_id)
- **GIVEN** a user exists with github_id "12345"
- **WHEN** GitHub callback returns with github user id "12345"
- **THEN** the existing user is logged in
- **AND** a session is created

#### Scenario: GitHub callback with auto-link by email
- **GIVEN** a user exists with email "user@example.com" but no github_id
- **WHEN** GitHub callback returns with email "user@example.com" and github_id "12345"
- **THEN** the user's github_id is set to "12345"
- **AND** the user is logged in

#### Scenario: GitHub callback with no matching user
- **WHEN** GitHub callback returns with email "newuser@example.com"
- **AND** no user exists with that email or github_id
- **THEN** response redirects to login page with error "Account not found. Contact admin."
- **AND** no session is created

---

### Requirement: Session Management
The system SHALL manage sessions in PostgreSQL with configurable lifetime.

#### Scenario: Session creation
- **WHEN** a user successfully authenticates
- **THEN** a session record is created with unique ID
- **AND** expires_at is set to NOW() + session_lifetime_days
- **AND** session ID is stored in a secure HTTP-only cookie

#### Scenario: Session validation
- **GIVEN** a request with session cookie
- **WHEN** the session exists and expires_at > NOW()
- **THEN** the user is considered authenticated

#### Scenario: Session expiration
- **GIVEN** a request with session cookie
- **WHEN** the session's expires_at < NOW()
- **THEN** the session is deleted
- **AND** the user is considered unauthenticated

#### Scenario: Session cleanup
- **WHEN** a background job runs (daily)
- **THEN** all sessions where expires_at < NOW() are deleted

---

### Requirement: Anonymous User Access
The system SHALL allow anonymous users to access chat functionality without authentication.

#### Scenario: Anonymous user identification
- **GIVEN** a request without authentication
- **WHEN** accessing /api/v2/chat
- **THEN** a temporary anon_id is generated (UUID)
- **AND** stored in session cookie
- **AND** user_id is set to "anon:{uuid}"

#### Scenario: Anonymous user limitations
- **GIVEN** an anonymous user
- **WHEN** accessing /api/v2/user/preferences
- **THEN** response is 401 with {error: "Authentication required"}

---

### Requirement: Admin User Management
The system SHALL allow admins to create and manage user accounts.

#### Scenario: Admin creates local user
- **GIVEN** an admin is authenticated
- **WHEN** POST /api/v2/admin/users with {email, password, display_name}
- **THEN** a user is created with hashed password
- **AND** is_admin defaults to false
- **AND** response is 201 with user info (no password)

#### Scenario: Admin promotes user to admin
- **GIVEN** an admin is authenticated
- **WHEN** PUT /api/v2/admin/users/:id with {is_admin: true}
- **THEN** the user's is_admin is set to true

#### Scenario: Non-admin attempts user management
- **GIVEN** a non-admin user is authenticated
- **WHEN** POST /api/v2/admin/users
- **THEN** response is 403 with {error: "Admin access required"}

#### Scenario: Admin deletes user
- **GIVEN** an admin is authenticated
- **WHEN** DELETE /api/v2/admin/users/:id
- **THEN** the user is deleted
- **AND** their sessions are deleted

---

### Requirement: CLI Setup Wizard
The system SHALL provide an interactive setup wizard for initial configuration.

#### Scenario: Interactive setup
- **WHEN** running `a2rchi init --name mybot`
- **AND** no --yes flag is provided
- **THEN** user is prompted for admin email
- **AND** user is prompted for admin password (hidden input)
- **AND** user is prompted for GitHub OAuth config (optional)

#### Scenario: Non-interactive setup with flags
- **WHEN** running `a2rchi init --name mybot --yes --admin-email admin@x.com --admin-password secret`
- **THEN** admin account is created without prompts

#### Scenario: Non-interactive setup with env vars
- **GIVEN** A2RCHI_ADMIN_EMAIL and A2RCHI_ADMIN_PASSWORD are set
- **WHEN** running `a2rchi init --name mybot --yes`
- **THEN** admin account is created from env vars

#### Scenario: Admin exists on startup
- **GIVEN** A2RCHI_ADMIN_EMAIL=admin@example.com is set
- **WHEN** the application starts
- **THEN** user with that email is ensured to have is_admin=true

---

## Database Schema

### Sessions Table
```sql
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(200) REFERENCES users(id) ON DELETE CASCADE,
    data JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
```

### Users Table Updates
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(256);
ALTER TABLE users ADD COLUMN IF NOT EXISTS github_id VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS github_username VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0;

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_github_id ON users(github_id) WHERE github_id IS NOT NULL;
```

---

## Contracts

### AuthService

```python
class AuthService:
    def __init__(self, pg_config: Dict[str, Any]):
        """Initialize with PostgreSQL config."""
    
    def login(self, email: str, password: str) -> Tuple[User, str]:
        """
        Authenticate user with email/password.
        
        Returns: (User, session_id)
        Raises: AuthenticationError if credentials invalid
        """
    
    def logout(self, session_id: str) -> None:
        """Delete session."""
    
    def create_session(self, user_id: str) -> str:
        """
        Create new session for user.
        
        Returns: session_id
        """
    
    def validate_session(self, session_id: str) -> Optional[User]:
        """
        Validate session and return user if valid.
        
        Returns: User if valid, None if expired/invalid
        """
    
    def github_callback(self, code: str, state: str) -> Tuple[User, str]:
        """
        Handle GitHub OAuth callback.
        
        Returns: (User, session_id)
        Raises: AuthenticationError if no matching user
        """
    
    def create_user(
        self, 
        email: str, 
        password: Optional[str] = None,
        display_name: Optional[str] = None,
        is_admin: bool = False
    ) -> User:
        """
        Create new user account. Admin only.
        
        Returns: Created user
        Raises: ValueError if email already exists
        """
    
    def ensure_admin(self, email: str) -> User:
        """
        Ensure user with email exists and is admin.
        Called on startup with A2RCHI_ADMIN_EMAIL.
        """
```

### Decorators

```python
def login_required(f):
    """Decorator requiring authenticated user (not anonymous)."""

def admin_required(f):
    """Decorator requiring admin user."""
```
