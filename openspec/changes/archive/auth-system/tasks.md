# Tasks: Authentication System

## Phase 1: Database & Foundation

- [ ] 1.1 Add auth columns to users table (password_hash, github_id, github_username, is_admin, last_login_at, login_count)
- [ ] 1.2 Create sessions table
- [ ] 1.3 Create `src/auth/` module structure
- [ ] 1.4 Implement AuthService class with PostgreSQL connection
- [ ] 1.5 Add authlib and flask-login to requirements

## Phase 2: Local Authentication

- [ ] 2.1 Implement password hashing (Werkzeug pbkdf2)
- [ ] 2.2 Implement `AuthService.login()` 
- [ ] 2.3 Implement `AuthService.logout()`
- [ ] 2.4 Implement `AuthService.create_session()`
- [ ] 2.5 Implement `AuthService.validate_session()`
- [ ] 2.6 Create `/auth/login` endpoint
- [ ] 2.7 Create `/auth/logout` endpoint
- [ ] 2.8 Create `/auth/me` endpoint
- [ ] 2.9 Integrate Flask-Login with session validation
- [ ] 2.10 Write tests for local auth flow

## Phase 3: Admin User Management

- [ ] 3.1 Implement `AuthService.create_user()` 
- [ ] 3.2 Implement `AuthService.ensure_admin()`
- [ ] 3.3 Create `@admin_required` decorator
- [ ] 3.4 Create `/api/v2/admin/users` GET endpoint (list users)
- [ ] 3.5 Create `/api/v2/admin/users` POST endpoint (create user)
- [ ] 3.6 Create `/api/v2/admin/users/:id` PUT endpoint (update user)
- [ ] 3.7 Create `/api/v2/admin/users/:id` DELETE endpoint (delete user)
- [ ] 3.8 Write tests for admin endpoints

## Phase 4: GitHub OAuth

- [ ] 4.1 Configure Authlib OAuth client for GitHub
- [ ] 4.2 Implement `AuthService.github_callback()`
- [ ] 4.3 Create `/auth/github` endpoint (initiate OAuth)
- [ ] 4.4 Create `/auth/github/callback` endpoint
- [ ] 4.5 Implement auto-link by email logic
- [ ] 4.6 Write tests for GitHub OAuth flow (mocked)

## Phase 5: Anonymous Users

- [ ] 5.1 Implement anonymous user middleware (`@app.before_request`)
- [ ] 5.2 Set `g.user_id` and `g.is_anonymous` for all requests
- [ ] 5.3 Update chat endpoints to use `g.user_id`
- [ ] 5.4 Add `@login_required` to protected endpoints
- [ ] 5.5 Write tests for anonymous access

## Phase 6: CLI Setup Wizard

- [ ] 6.1 Add `--admin-email` and `--admin-password` flags to `a2rchi init`
- [ ] 6.2 Implement interactive prompts (when no --yes flag)
- [ ] 6.3 Read A2RCHI_ADMIN_EMAIL and A2RCHI_ADMIN_PASSWORD env vars
- [ ] 6.4 Add GitHub OAuth config prompts (client_id, client_secret)
- [ ] 6.5 Store GitHub OAuth secrets securely
- [ ] 6.6 Call `ensure_admin()` on application startup
- [ ] 6.7 Write tests for CLI setup (non-interactive mode)

## Phase 7: Session Cleanup & Hardening

- [ ] 7.1 Implement session cleanup job (delete expired sessions)
- [ ] 7.2 Add session cleanup to scheduler or startup
- [ ] 7.3 Configure secure cookie settings (HTTPOnly, Secure, SameSite)
- [ ] 7.4 Add CSRF protection for auth endpoints
- [ ] 7.5 Add rate limiting for login endpoint (future consideration)

## Phase 8: Integration & Documentation

- [ ] 8.1 Update all protected endpoints to use `@login_required` or `@admin_required`
- [ ] 8.2 Update frontend for login UI
- [ ] 8.3 Update API documentation
- [ ] 8.4 Update user guide with auth setup instructions
- [ ] 8.5 Add troubleshooting guide for auth issues
