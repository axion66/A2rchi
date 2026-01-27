# Project Context

## Purpose
A2rchi is an AI agent designed for the operations of large-scale scientific experiments. Initiated at MIT with resources from CERN, it aims to evolve from a passive retrieval assistant into an autonomous scientist.

## Vision Roadmap
- **Phase A (Current):** Passive Agent. Retrieval-augmented generation (RAG) for chat over organizational information (docs, wikis, code).
- **Phase B:** Expanded Modalities. Integration with scientific experiment data sources, including real-time streaming data and system logs.
- **Phase C:** Active Agent. Capability to use tools that modify state, execute code, and assist in complex data analysis.
- **Phase D:** Autonomous Scientist. Full capability to engage in scientific research autonomously.

## Tech Stack
- **Languages:** Python (Core), TypeScript/JavaScript (Web/Extensions)
- **Core Frameworks:** LangChain (likely), Flask/FastAPI (Services), ChromaDB/Postgres (Vector Store)
- **Infrastructure:** Docker, Kubernetes (implied by "large scale"), GPU acceleration support

## Project Conventions

### Code Style
- Python: PEP 8, formatted with `isort` and `black`.
- Commits: Concise, descriptive, lowercase summaries.

### Architecture Patterns
- **Services:** Modular microservices in `src/bin/` wiring together core logic.
- **Orchestration:** `src/a2rchi/a2rchi.py` controls the central agent loop.
- **Configuration:** Runtime config loaded from `/root/A2rchi/configs/`.

## Domain Context
- **Scientific Operations:** The system must handle the rigor, scale, and specific modalities of scientific experiments (e.g., particle physics, large sensor arrays).
- **Security:** As an operations agent, it requires robust auth and permission handling (currently being specced/implemented).

## External Dependencies
- **LLM Providers:** OpenAI, Anthropic, or local models via Ollama/vLLM.
- **Data Sources:** Git, Websites, JIRA, Confluence, Local Files.
