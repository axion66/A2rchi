# Multi-Provider Model Support

## Summary
Add support for multiple LLM providers (OpenAI, OpenRouter, Gemini, Anthropic, local server) with runtime switching via the Settings UI. Introduce clean abstractions for model providers and agents to enable flexible configuration.

## Motivation
Currently A2rchi is tightly coupled to a single model provider configuration. Users need the flexibility to:
- Switch between providers based on cost, availability, or capability requirements
- Use local LLMs for privacy-sensitive deployments
- Compare responses from different providers
- Access different agent configurations per use case

## Proposed Changes

### 1. Provider Abstraction Layer

Create a unified interface for model providers:

```
src/a2rchi/providers/
├── __init__.py
├── base.py              # Abstract BaseProvider class
├── openai_provider.py   # OpenAI (GPT-4, GPT-4o, etc.)
├── openrouter_provider.py  # OpenRouter (access to many models)
├── gemini_provider.py   # Google Gemini
├── anthropic_provider.py   # Anthropic Claude
└── local_provider.py    # Local LLM server (Ollama, vLLM, etc.)
```

**BaseProvider Interface:**
```python
class BaseProvider(ABC):
    @abstractmethod
    def get_chat_model(self, model_name: str, **kwargs) -> BaseChatModel
    
    @abstractmethod
    def get_embeddings(self, model_name: str, **kwargs) -> Embeddings
    
    @abstractmethod
    def list_models(self) -> List[ModelInfo]
    
    @abstractmethod
    def validate_api_key(self) -> bool
```

### 2. Agent Abstraction Layer

Decouple agents from models:

```
src/a2rchi/agents/
├── __init__.py
├── base.py              # Abstract BaseAgent class
├── react_agent.py       # ReAct-style tool-using agent
├── simple_agent.py      # Direct LLM without tools
└── registry.py          # Agent registration and discovery
```

**BaseAgent Interface:**
```python
class BaseAgent(ABC):
    def __init__(self, provider: BaseProvider, model_name: str, tools: List[Tool])
    
    @abstractmethod
    async def invoke(self, messages: List, config: AgentConfig) -> AsyncIterator[Event]
    
    @property
    @abstractmethod
    def capabilities(self) -> AgentCapabilities
```

### 3. Configuration Schema Updates

**Provider Configuration (config.yaml):**
```yaml
providers:
  openai:
    enabled: true
    api_key_env: "OPENAI_API_KEY"
    models:
      - name: "gpt-4o"
        display_name: "GPT-4o"
        context_window: 128000
      - name: "gpt-4o-mini"
        display_name: "GPT-4o Mini"
        context_window: 128000
        
  openrouter:
    enabled: true
    api_key_env: "OPENROUTER_API_KEY"
    models:
      - name: "anthropic/claude-3.5-sonnet"
        display_name: "Claude 3.5 Sonnet (via OpenRouter)"
      - name: "google/gemini-pro"
        display_name: "Gemini Pro (via OpenRouter)"
        
  anthropic:
    enabled: true
    api_key_env: "ANTHROPIC_API_KEY"
    models:
      - name: "claude-sonnet-4-20250514"
        display_name: "Claude Sonnet 4"
        
  gemini:
    enabled: true
    api_key_env: "GOOGLE_API_KEY"
    models:
      - name: "gemini-2.0-flash"
        display_name: "Gemini 2.0 Flash"
        
  local:
    enabled: false
    base_url: "http://localhost:11434/v1"
    models:
      - name: "llama3.3"
        display_name: "Llama 3.3 70B (Local)"

agents:
  - name: "cms_assistant"
    display_name: "CMS Computing Assistant"
    description: "Tool-using agent with knowledge base access"
    type: "react"
    default_provider: "openai"
    default_model: "gpt-4o"
    tools:
      - search_vectorstore_hybrid
      - search_local_files
      - search_metadata_index
      - fetch_catalog_document
      
  - name: "simple_chat"
    display_name: "Simple Chat"
    description: "Direct conversation without tools"
    type: "simple"
    default_provider: "anthropic"
    default_model: "claude-sonnet-4-20250514"
    tools: []
```

### 4. API Endpoint Updates

**New Endpoints:**
```
GET  /api/providers          # List enabled providers with their models
GET  /api/agents             # List available agents
POST /api/set_provider       # Set active provider for session
POST /api/set_agent          # Set active agent for session
GET  /api/session_config     # Get current provider/agent/model selection
```

**Updated `/api/get_configs` response:**
```json
{
  "providers": [
    {
      "id": "openai",
      "name": "OpenAI",
      "models": [
        {"id": "gpt-4o", "name": "GPT-4o", "context_window": 128000}
      ]
    }
  ],
  "agents": [
    {
      "id": "cms_assistant",
      "name": "CMS Computing Assistant",
      "description": "...",
      "supports_tools": true
    }
  ],
  "current": {
    "provider": "openai",
    "model": "gpt-4o",
    "agent": "cms_assistant"
  }
}
```

### 5. Settings UI Updates

**Settings Modal Sections:**

```
┌─────────────────────────────────────────┐
│ Settings                            [X] │
├─────────────────────────────────────────┤
│ Model Provider                          │
│ ┌─────────────────────────────────────┐ │
│ │ ▼ OpenAI                            │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Model                                   │
│ ┌─────────────────────────────────────┐ │
│ │ ▼ GPT-4o                            │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ─────────────────────────────────────── │
│                                         │
│ Agent                                   │
│ ┌─────────────────────────────────────┐ │
│ │ ▼ CMS Computing Assistant           │ │
│ └─────────────────────────────────────┘ │
│ ℹ Tool-using agent with knowledge base │
│                                         │
│ ─────────────────────────────────────── │
│                                         │
│ A/B Testing                             │
│ [Toggle] Enable A/B comparison          │
│                                         │
│ Agent Transparency                      │
│ ○ Minimal  ○ Normal  ○ Verbose         │
└─────────────────────────────────────────┘
```

### 6. Input Area Updates

Show current selection clearly:

```
┌──────────────────────────────────────────────────┐
│ Ask A2rchi...                                    │
├──────────────────────────────────────────────────┤
│ GPT-4o (OpenAI) · CMS Assistant    [⚙] [Send]   │
└──────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Provider Abstraction (Backend)
1. Create `BaseProvider` interface
2. Implement OpenAI provider (extract from existing code)
3. Add provider configuration schema
4. Update `ChatWrapper` to use provider abstraction

### Phase 2: Additional Providers (Backend)
1. Implement Anthropic provider
2. Implement Gemini provider
3. Implement OpenRouter provider
4. Implement Local server provider
5. Add provider health checks

### Phase 3: Agent Abstraction (Backend)
1. Create `BaseAgent` interface
2. Refactor existing ReAct agent to use interface
3. Create simple (non-tool) agent
4. Add agent registry

### Phase 4: API Updates
1. Add `/api/providers` endpoint
2. Add `/api/agents` endpoint
3. Add `/api/set_provider` and `/api/set_agent`
4. Update streaming to use selected provider/agent

### Phase 5: Frontend Updates
1. Update Settings modal with provider/model selectors
2. Add agent selector
3. Update input area to show current selection
4. Persist selection to localStorage
5. Update A/B testing to work with multiple providers

### Phase 6: Documentation & Testing
1. Update configuration documentation
2. Add provider setup guides
3. Write integration tests for each provider
4. Add smoke tests for provider switching

## File Changes Summary

**New Files:**
- `src/a2rchi/providers/base.py`
- `src/a2rchi/providers/openai_provider.py`
- `src/a2rchi/providers/anthropic_provider.py`
- `src/a2rchi/providers/gemini_provider.py`
- `src/a2rchi/providers/openrouter_provider.py`
- `src/a2rchi/providers/local_provider.py`
- `src/a2rchi/agents/base.py`
- `src/a2rchi/agents/react_agent.py`
- `src/a2rchi/agents/simple_agent.py`
- `src/a2rchi/agents/registry.py`

**Modified Files:**
- `src/a2rchi/a2rchi.py` - Use provider/agent abstractions
- `src/interfaces/chat_app/app.py` - New API endpoints
- `src/interfaces/chat_app/static/chat.js` - Settings UI updates
- `src/interfaces/chat_app/static/chat.css` - New selector styles
- `src/interfaces/chat_app/templates/index.html` - Settings form updates
- `src/utils/config_loader.py` - Load provider/agent configs

## Security Considerations

1. **API Keys**: Store in environment variables, never in config files
2. **Provider Selection**: Validate provider is enabled before use
3. **Rate Limiting**: Consider per-provider rate limits
4. **Local Server**: Ensure local provider can't be enabled in cloud deployments without explicit configuration

## Open Questions

1. Should provider selection persist per-conversation or globally?
2. Should A/B testing allow cross-provider comparisons?
3. How should embeddings provider be handled (separate from chat provider)?
4. Should there be admin-only providers vs user-selectable providers?
