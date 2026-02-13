# Models & Providers

Archi uses a **provider-based architecture** for LLM access. Each provider wraps a specific LLM service and exposes a unified interface for model listing, connection validation, and chat model creation.

## Provider Architecture

All providers extend the `BaseProvider` abstract class and are registered in a global provider registry. The system supports five provider types:

| Provider | Type | API Key Env Var | Default Model | LangChain Backend |
|----------|------|----------------|---------------|-------------------|
| OpenAI | `openai` | `OPENAI_API_KEY` | `gpt-4o` | `ChatOpenAI` |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` | `claude-sonnet-4-20250514` | `ChatAnthropic` |
| Google Gemini | `gemini` | `GOOGLE_API_KEY` | `gemini-2.0-flash` | `ChatGoogleGenerativeAI` |
| OpenRouter | `openrouter` | `OPENROUTER_API_KEY` | `anthropic/claude-3.5-sonnet` | `ChatOpenAI` (custom base URL) |
| Local (Ollama/vLLM) | `local` | N/A | Dynamic (fetched from server) | `ChatOllama` or `ChatOpenAI` |

### Key Concepts

- **`ProviderType`**: An enum of supported provider names (`OPENAI`, `ANTHROPIC`, `GEMINI`, `OPENROUTER`, `LOCAL`).
- **`ProviderConfig`**: A dataclass holding provider settings — type, API key, base URL, enabled state, models list, and extra kwargs.
- **`ModelInfo`**: Describes a model's capabilities — context window, tool support, streaming support, vision support, and max output tokens.
- **Provider Registry**: Providers are lazily registered at first use. Factory functions (`get_provider`, `get_model`) handle instantiation and caching.

---

## Configuring Providers

Providers are configured per-service in your deployment's configuration file. Each service can specify a default provider and model, plus provider-specific settings.

### OpenAI

```yaml
services:
  chat_app:
    provider: openai
    model: gpt-4o
```

**Secrets:**

```bash
OPENAI_API_KEY=sk-...
```

### Anthropic

```yaml
services:
  chat_app:
    provider: anthropic
    model: claude-sonnet-4-20250514
```

**Secrets:**

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

### Google Gemini

```yaml
services:
  chat_app:
    provider: gemini
    model: gemini-2.0-flash
    providers:
      gemini:
        enabled: true
```

Available models: `gemini-2.0-flash`, `gemini-2.0-flash-thinking`, `gemini-1.5-pro`, `gemini-1.5-flash`.

**Secrets:**

```bash
GOOGLE_API_KEY=AIza...
```

### OpenRouter

OpenRouter uses an OpenAI-compatible API to access models from multiple providers. No special config entry is required — if `OPENROUTER_API_KEY` is set, the provider appears automatically in the chat UI.

To make OpenRouter the default:

```yaml
services:
  chat_app:
    provider: openrouter
    model: anthropic/claude-3.5-sonnet
```

**Secrets:**

```bash
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_SITE_URL=https://your-site.com    # optional, for attribution
OPENROUTER_APP_NAME=My Archi Instance        # optional, for attribution
```

### Local Models (Ollama)

Run open-source models locally via [Ollama](https://ollama.ai):

```yaml
services:
  chat_app:
    provider: local
    model: llama3.2
    providers:
      local:
        base_url: http://localhost:11434
        mode: ollama
        models:
          - llama3.2
```

The `local` provider supports two modes:

- **`ollama`** (default): Uses `ChatOllama`. Models are dynamically fetched from the Ollama server's `/api/tags` endpoint.
- **`openai_compat`**: Uses `ChatOpenAI` with a custom base URL. Suitable for vLLM, LM Studio, or other OpenAI-compatible servers.

For `openai_compat` mode:

```yaml
services:
  chat_app:
    provider: local
    model: my-model
    providers:
      local:
        base_url: http://localhost:8000/v1
        mode: openai_compat
        models:
          - my-model
```

> **Note:** For GPU setup with local models, see [Advanced Setup & Deployment](advanced_setup_deploy.md#running-llms-locally-on-your-gpus).

---

## Embedding Models

Embeddings convert text into numerical vectors for semantic search. Configure these in the `data_manager` section:

### OpenAI Embeddings

```yaml
data_manager:
  embedding_name: OpenAIEmbeddings
  embedding_class_map:
    OpenAIEmbeddings:
      class: OpenAIEmbeddings
      kwargs:
        model: text-embedding-3-small
      similarity_score_reference: 10
```

Requires `OPENAI_API_KEY` in your secrets file.

### HuggingFace Embeddings

```yaml
data_manager:
  embedding_name: HuggingFaceEmbeddings
  embedding_class_map:
    HuggingFaceEmbeddings:
      class: HuggingFaceEmbeddings
      kwargs:
        model_name: sentence-transformers/all-MiniLM-L6-v2
        model_kwargs:
          device: cpu
        encode_kwargs:
          normalize_embeddings: true
      similarity_score_reference: 10
```

Uses HuggingFace models locally. Optionally requires `HUGGINGFACEHUB_API_TOKEN` for private models.

---

## Bring Your Own Key (BYOK)

BYOK allows users to provide their own API keys for LLM providers at runtime, enabling cost attribution, provider flexibility, and privacy.

### Key Hierarchy

API keys are resolved in the following order (highest priority first):

1. **Environment Variables**: Admin-configured keys (e.g., `OPENAI_API_KEY`)
2. **Docker Secrets**: Keys mounted at `/run/secrets/`
3. **Session Storage**: User-provided keys via the Settings UI

> **Note:** Environment variable keys always take precedence. If an admin configures a key via an environment variable, users cannot override it.

### Using BYOK in the Chat Interface

1. Open the **Settings** modal (gear icon in the header)
2. Expand the **API Keys** section
3. Enter your API key for each provider you want to use
4. Click **Save** to store it in your session
5. Select your preferred **Provider** and **Model** from the dropdowns
6. Start chatting

**Status Indicators:**

| Icon | Meaning |
|------|---------|
| ✓ Env | Key configured via environment variable (cannot be changed) |
| ✓ Session | Key configured via your session |
| ○ | No key configured |

### BYOK API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/providers/keys` | GET | Get status of all provider keys |
| `/api/providers/keys/set` | POST | Set a session API key (validates before storing) |
| `/api/providers/keys/clear` | POST | Clear a session API key |

### Security Considerations

- Keys are never logged or echoed
- Keys are session-scoped and cleared on logout or session expiry
- HTTPS is strongly recommended for production — see [HTTPS Configuration](advanced_setup_deploy.md#https-configuration-for-production)
