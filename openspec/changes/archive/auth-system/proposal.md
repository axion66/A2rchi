# Proposal: Authentication System

## Problem Statement

A2rchi currently has fragmented, incomplete authentication:

1. **Optional auth** - Can be disabled entirely (`auth.enabled: false`)
2. **Multiple half-implementations** - SSO config exists but unclear if working
3. **Basic auth** - Password-based, stored where?
4. **Anonymous users** - Generated client IDs, no upgrade path
5. **No admin concept** - Anyone can do anything (or no one can)

The config-management proposal requires:
- Authenticated users with persistent identity
- Admin role for deployment-level settings
- BYOK API keys tied to user accounts

## Proposed Solution

Implement proper authentication using a well-established library with:
- Single Sign-On (SSO) via GitHub OAuth2
- Local accounts (admin-created only)
- Clear admin designation via setup wizard
- Session management in PostgreSQL
- Anonymous access preserved (full functionality, no persistence)

## Resolved Decisions

| Question | Decision |
|----------|----------|
| First admin | Setup wizard + `A2RCHI_ADMIN_EMAIL` env var fallback |
| Anonymous access | Full functionality, no persistence |
| SSO providers | GitHub initially |
| Local accounts | Always available, admin-created only |
| API auth | Same as web (session cookies) |
| Registration | Admin-controlled (no self-signup) |
| Account linking | Auto-link GitHub to local account by email |

## Requirements

### Must Have
- [x] User authentication (login/logout)
- [x] Admin role with clear designation
- [x] Session management (cookies in PostgreSQL)
- [x] User identity persistence across sessions
- [x] Works with PostgreSQL user table
- [x] CLI setup wizard with non-interactive mode

### Should Have
- [x] GitHub OAuth support
- [x] Local account creation (admin only)
- [x] Password hashing (Werkzeug pbkdf2)
- [x] Session timeout configuration

### Won't Have (this proposal)
- Multi-factor authentication
- API key authentication for programmatic access
- Rate limiting per user
- Role-based access control beyond admin/user

## Library Stack

```
Authlib          → GitHub OAuth2 flow
Flask-Login      → Session management, @login_required
Werkzeug         → Password hashing (pbkdf2)
```

## Success Criteria

- [ ] All protected endpoints require authentication
- [ ] Admin can be designated via setup wizard or env var
- [ ] GitHub login works
- [ ] Local accounts work (admin creates them)
- [ ] Sessions persist in PostgreSQL
- [ ] Anonymous users can chat but have no persistence
- [ ] Logout invalidates session
