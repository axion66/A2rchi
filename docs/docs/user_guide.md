# User Guide

This guide covers the core concepts and features of Archi. Each topic has its own dedicated page for detailed reference.

## Overview

Archi is organized around three core concepts:

- **Data Sources**: How you ingest content into the vector store for retrieval
- **Services**: Containerized applications that interact with the AI pipelines
- **Agents & Pipelines**: AI assistants with configurable tools and prompts

Both data sources and services are enabled via flags to the `archi create` command:

```bash
archi create [...] --services chatbot,uploader --sources git,jira --agents examples/agents
```

Configuration details for each are set in a YAML configuration file. See the [Configuration Reference](configuration.md) for the full schema.

---

## Data Sources

Archi supports several data ingestion methods:

- **Web link lists** (including SSO-protected pages)
- **Git scraping** for MkDocs-based repositories
- **JIRA** and **Redmine** ticketing systems
- **Manual document upload** via the Uploader service or direct file copy
- **Local documents**

Sources are configured under `data_manager.sources` in your config file and enabled with `--sources` at deploy time.

**[Read more →](data_sources.md)**

---

## Services

Archi provides these deployable services:

| Service | Description | Default Port |
|---------|-------------|-------------|
| `chatbot` | Web-based chat interface | 7861 |
| `data_manager` | Data ingestion and vectorstore management | 7871 |
| `piazza` | Piazza forum integration with Slack | — |
| `redmine-mailer` | Redmine ticket responses via email | — |
| `mattermost` | Mattermost channel integration | — |
| `grafana` | Monitoring dashboard | 3000 |
| `grader` | Automated grading service | 7862 |

**[Read more →](services.md)**

---

## Agents & Tools

Agents are defined by **agent specs** — Markdown files with YAML frontmatter specifying name, tools, and system prompt. Agent specs are passed to the CLI via `--agents`.

The default agent class (`CMSCompOpsAgent`) provides tools for:

- Metadata and content search across ingested documents
- Hybrid semantic + BM25 vector store retrieval
- Full document fetching by hash
- External tools via MCP (Model Context Protocol)

**[Read more →](agents_tools.md)**

---

## Models & Providers

Archi supports five LLM provider types:

| Provider | Models |
|----------|--------|
| OpenAI | GPT-4o, GPT-4, etc. |
| Anthropic | Claude 4, Claude 3.5 Sonnet, etc. |
| Google Gemini | Gemini 2.0 Flash, Gemini 1.5 Pro, etc. |
| OpenRouter | Access to 100+ models via a unified API |
| Local (Ollama/vLLM) | Any open-source model |

Users can also provide their own API keys at runtime via **Bring Your Own Key (BYOK)**.

**[Read more →](models_providers.md)**

---

## Configuration Management

Archi uses a three-tier configuration system:

1. **Static Configuration** (deploy-time, immutable): deployment name, embedding model, available pipelines
2. **Dynamic Configuration** (admin-controlled, runtime-modifiable): default model, temperature, retrieval parameters
3. **User Preferences** (per-user overrides): preferred model, temperature, prompt selections

Settings are resolved as: User Preference → Dynamic Config → Static Default.

See the [Configuration Reference](configuration.md) for the full YAML schema and the [API Reference](api_reference.md) for the configuration API.

---

## Secrets

Secrets are stored in a `.env` file passed via `--env-file`. Required secrets depend on your deployment:

| Secret | Required For |
|--------|-------------|
| `PG_PASSWORD` | All deployments |
| `OPENAI_API_KEY` | OpenAI provider |
| `ANTHROPIC_API_KEY` | Anthropic provider |
| `GOOGLE_API_KEY` | Google Gemini provider |
| `OPENROUTER_API_KEY` | OpenRouter provider |
| `HUGGINGFACEHUB_API_TOKEN` | Private HuggingFace models |
| `GIT_USERNAME` / `GIT_TOKEN` | Git source |
| `JIRA_PAT` | JIRA source |
| `REDMINE_USER` / `REDMINE_PW` | Redmine source |

See [Data Sources](data_sources.md) and [Services](services.md) for service-specific secrets.

---

## Benchmarking

Archi has benchmarking functionality via the `archi evaluate` CLI command:

- **SOURCES mode**: Checks if retrieved documents contain the correct sources
- **RAGAS mode**: Uses the Ragas evaluator for answer relevancy, faithfulness, context precision, and context relevancy

**[Read more →](benchmarking.md)**

---

## Prompt Customization

Prompts are stored as `.prompt` files in your deployment directory. Archi supports three prompt types:

- **condense**: Condensing conversation history
- **chat**: Main response generation
- **system**: System-level instructions

Prompts can be set per-deployment (admin) or per-user via the API.

```
~/.archi/<deployment-name>/data/prompts/
├── condense/
│   └── default.prompt
├── chat/
│   └── default.prompt
└── system/
    └── default.prompt
```

See the [API Reference](api_reference.md#prompts) for prompt management endpoints.

---

## Admin Guide

### Becoming an Admin

Set admin status in PostgreSQL:

```sql
UPDATE users SET is_admin = true WHERE email = 'admin@example.com';
```

### Admin Capabilities

- Set deployment-wide defaults via the dynamic configuration API
- Manage prompts (add, edit, reload via API)
- View the configuration audit log
- Grant admin privileges to other users

### Audit Logging

All admin configuration changes are logged and queryable:

```
GET /api/config/audit?limit=50
```

See the [API Reference](api_reference.md#configuration) for full endpoint documentation.
