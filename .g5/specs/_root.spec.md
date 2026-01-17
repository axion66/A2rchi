---
spec_id: root
type: root
status: extracted
children:
  - a2rchi
  - data-manager
  - cli
  - interfaces
  - bin
  - utils
---

# A2rchi

> LLM-powered question-answering and grading framework with RAG support.

## Package Hierarchy

```
src/
├── a2rchi/              # Core LLM orchestration
│   ├── core             # A2rchi class
│   ├── models/          # 8 LLM implementations
│   └── pipelines/       # 4 pipelines + utils
│
├── data_manager/        # Document management
│   ├── core             # DataManager class
│   ├── collectors/      # Web scraping, tickets
│   └── vectorstore/     # Embeddings + retrieval
│
├── cli/                 # Deployment CLI
│   ├── commands         # Click commands
│   ├── managers/        # Docker/compose
│   └── utilities/       # Helpers
│
├── interfaces/          # User applications
│   ├── chat_app/        # Web chat (Flask)
│   ├── grader_app/      # AI grading (Flask)
│   └── integrations     # Piazza, Mattermost
│
├── bin/                 # Service entry points
│   └── services         # service_*.py scripts
│
└── utils/               # Shared utilities
    ├── config_loader    # YAML config
    ├── logging          # Centralized logging
    └── env              # Secret management
```

## Spec Inventory

| Module | Specs | Description |
|--------|-------|-------------|
| `a2rchi/` | 1 + 8 + 8 = 17 | Core + models + pipelines |
| `data-manager/` | 7 | Data collection + vectorstore |
| `cli/` | 5 | Deployment commands |
| `interfaces/` | 5 | Web apps + bots |
| `bin/` | 1 | Service runners |
| `utils/` | 5 | Shared utilities |
| **Total** | **40** | |

## Key Abstractions

1. **A2rchi** - Central orchestrator connecting everything
2. **Pipeline** - Task-specific LLM workflows (QA, Grading)
3. **Model** - LLM interface (OpenAI, HuggingFace, etc.)
4. **DataManager** - Document ingestion + vectorstore
5. **Collector** - Data source integration protocol

## Data Flow

```
User Request
     │
     ▼
┌──────────┐     ┌────────────┐     ┌──────────┐
│Interface │────▶│   A2rchi   │────▶│ Pipeline │
└──────────┘     └─────┬──────┘     └────┬─────┘
                       │                  │
                       ▼                  ▼
              ┌─────────────┐      ┌───────────┐
              │ Vectorstore │◀─────│   Model   │
              └─────────────┘      └───────────┘
```

## Configuration

Single YAML config drives everything:

```yaml
a2rchi:
  pipeline_map: { ... }
  model_class_map: { ... }

data_manager:
  sources: { links: {...}, tickets: {...} }
  vectorstore: { type: "chroma" }

services:
  chat_app: { pipeline: "QAPipeline" }
```

## Installation

```bash
pip install -e .
a2rchi init my-deployment
a2rchi up
```
