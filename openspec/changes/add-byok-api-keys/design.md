# BYOK Design Document

## Context

A2rchi supports multiple LLM providers (OpenAI, Anthropic, Gemini, OpenRouter, Local). Each provider requires an API key for authentication. Currently, keys are configured at deployment time via environment variables. This works for simple deployments but doesn't support:

- End-users bringing their own API keys
- Users trying different providers without admin access
- Cost attribution to individual users
- Privacy-conscious users preferring their own accounts

## Goals / Non-Goals

### Goals
- Allow users to provide their own API keys at runtime
- Maintain backwards compatibility with environment variable configuration
- Provide clear UX for key status and management
- Keep keys secure in transit and at rest
- Support multiple key sources with clear precedence

### Non-Goals
- Storing keys permanently in a database (session-only for this iteration)
- Per-user key persistence across sessions (future work)
- Key rotation/expiration management (out of scope)
- Third-party secrets manager integration (users can pre-populate env vars)

## Key Hierarchy

```
┌─────────────────────────────────────────────────────┐
│  1. Environment Variable (highest priority)         │
│     OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.        │
├─────────────────────────────────────────────────────┤
│  2. Docker Secrets (if available)                   │
│     /run/secrets/openai_api_key, etc.              │
├─────────────────────────────────────────────────────┤
│  3. Session Storage (user-provided via UI)          │
│     Encrypted Flask session, cleared on logout      │
└─────────────────────────────────────────────────────┘
```

**Rationale**: Environment variables take precedence because:
- Admin-configured keys should not be overridable by users
- Deployments with pre-configured keys "just work"
- Session keys are a fallback for user flexibility

## API Design

### GET /api/providers/keys
Returns status of API keys for all enabled providers.

**Response:**
```json
{
  "providers": [
    {
      "id": "openai",
      "name": "OpenAI",
      "has_key": true,
      "source": "env",      // "env" | "session" | null
      "can_override": false  // true if admin allows session override
    },
    {
      "id": "anthropic", 
      "name": "Anthropic",
      "has_key": false,
      "source": null,
      "can_override": true
    }
  ]
}
```

### POST /api/providers/keys/set
Sets an API key in session storage.

**Request:**
```json
{
  "provider": "anthropic",
  "api_key": "sk-ant-..."
}
```

**Response:**
```json
{
  "success": true,
  "provider": "anthropic",
  "source": "session"
}
```

**Error Cases:**
- Provider not found: 404
- Provider locked to env-only: 403
- Invalid key format: 400

### POST /api/providers/keys/clear
Removes session-stored API key for a provider.

**Request:**
```json
{
  "provider": "anthropic"
}
```

### POST /api/providers/keys/validate
Validates an API key works with the provider.

**Request:**
```json
{
  "provider": "anthropic",
  "api_key": "sk-ant-..."
}
```

**Response:**
```json
{
  "valid": true,
  "provider": "anthropic",
  "models_available": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
}
```

## UI Design

### Settings Modal - API Keys Section

```
┌─────────────────────────────────────────────────────────┐
│  Settings                                         [X]   │
├─────────────────────────────────────────────────────────┤
│  Provider     Model                                     │
│  [OpenAI ▼]   [gpt-4o ▼]                               │
│                                                         │
│  ▼ API Keys                                            │
│  ┌─────────────────────────────────────────────────┐   │
│  │ OpenAI      ✓ ENV    [••••••••••••] [Clear]     │   │
│  │ Anthropic   ○        [sk-ant-...  ] [Set]       │   │
│  │ Gemini      ○        [AIza...     ] [Set]       │   │
│  │ OpenRouter  ✓ ENV    [••••••••••••] [Clear]     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ℹ Keys from ENV cannot be changed here.               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Status Indicators
- `✓ ENV` - Key configured via environment variable (green)
- `✓ SET` - Key configured via session (blue)
- `○` - No key configured (gray)

### Behavior
- Input field disabled when key source is "env"
- "Set" button validates key before storing
- "Clear" button only appears for session keys
- Collapsible section (default collapsed if all providers have env keys)

## Security Considerations

### Transport Security
- All API endpoints require HTTPS in production
- Session cookies marked Secure and HttpOnly
- API keys never in URL query parameters

### Storage Security
- Flask session uses server-side encrypted storage
- Session keys cleared on explicit logout
- Session timeout configurable (default: 24 hours)
- No client-side localStorage for keys

### Logging
- API keys redacted from all log output
- Key operations logged without key values
- Failed validation attempts rate-limited

### Input Validation
- Key format validated before storage
- Provider ID validated against enabled list
- Request size limits enforced

## Risks / Trade-offs

### Risk: Session expiry clears user keys
- **Mitigation**: Clear UI indicator when keys are session-based
- **Mitigation**: Consider future work for optional key persistence

### Risk: Users confused by key precedence
- **Mitigation**: Show key source clearly in UI
- **Mitigation**: Disable input for env-configured providers

### Risk: API key leaked via browser devtools
- **Mitigation**: Keys never returned in full from API
- **Mitigation**: Input masked, no autocomplete

### Trade-off: No key persistence vs UX convenience
- **Decision**: Start with session-only for security simplicity
- **Rationale**: Users needing persistence can use env vars
- **Future**: Database storage with encryption can be added later

## Migration Plan

1. **Phase 1**: Add session key storage (no breaking changes)
2. **Phase 2**: Add UI for key management
3. **Phase 3**: Add validation endpoint
4. **Phase 4**: Documentation and deployment guide updates

No migration required for existing deployments - env vars continue to work.

## Open Questions

1. Should we support key validation before allowing chat? (Currently: optional)
2. Should admins be able to disable BYOK entirely? (Currently: not implemented)
3. Should we add rate limiting per-user for key validation? (Currently: not implemented)
