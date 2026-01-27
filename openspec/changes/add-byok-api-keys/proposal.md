# Change: Add Bring Your Own Key (BYOK) API Key Management

## Why
Users deploying A2rchi need a flexible, secure way to provide their own API keys for different LLM providers. Currently, API keys must be configured at deployment time via environment variables, which limits end-users from using their own accounts or switching providers without admin intervention.

## What Changes
- Add session-based API key storage with clear precedence rules
- Implement secure API key input UI in Settings modal
- Add API endpoints for key management (get status, set, clear)
- Support key hierarchy: environment variables → Docker secrets → session storage
- Display clear status indicators showing key source (ENV, session, none)
- **BREAKING**: None - backwards compatible with existing env var configuration

## Impact
- Affected specs: New `byok` capability
- Affected code: 
  - `src/a2rchi/providers/base.py` - runtime key injection
  - `src/interfaces/chat_app/app.py` - key management endpoints
  - `src/interfaces/chat_app/static/chat.js` - key input UI
  - `src/interfaces/chat_app/templates/index.html` - Settings modal

## Design Principles

### Security First
1. **Keys never logged** - API keys are never written to logs or debug output
2. **Keys never echoed** - UI masks input and only shows status (configured/not)
3. **Session-scoped** - Session keys cleared on logout/expiry
4. **HTTPS required** - Production deployments must use TLS
5. **No client-side storage** - Keys stored server-side in encrypted sessions only

### Ease of Use
1. **Zero-config default** - Works with env vars for simple deployments
2. **Clear feedback** - Users see which providers have keys configured and from what source
3. **Non-destructive** - Setting a session key doesn't remove env var capability
4. **Provider-aware** - Only show providers that are enabled in the deployment

### Flexibility
1. **Multiple sources** - Supports env vars, Docker secrets, session, or future integrations
2. **Per-provider control** - Users can set keys for only the providers they need
3. **Admin override** - Deployment admins can lock providers to env-only mode
4. **No vendor lock-in** - Works with any secrets management approach
