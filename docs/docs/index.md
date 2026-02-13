# Archi

Archi (AI Augmented Research Chat Intelligence) is a retrieval-augmented generation (RAG) framework designed to be a low-barrier, open-source, private, and customizable AI solution for research and educational support.

Archi makes it easy to deploy AI assistants with a suite of tools that connect to

- communication platforms such as Piazza, Slack, Mattermost, and email, and
- knowledge bases such as web links, files, JIRA tickets, and documentation.

It is modular and extensible, allowing users to add connectors and customise pipeline behaviour for a wide range of tasks—from answering simple questions to delivering detailed explanations.

## About

Archi is an end-to-end framework developed by Prof. Paus (MIT Physics), Prof. Kraska (MIT EECS), and their students. It has already been successfully deployed as a user chatbot and technical assistant at SubMIT (the MIT Physics Department's private cluster) and as an educational assistant for several MIT courses, including 8.01 and 8.511.

What sets Archi apart is that it is fully open source, configurable across foundational models and LLM libraries, and designed for private deployment. Under the hood, Archi is a highly configurable RAG system tailored for educational and scientific support. Given its success, the scope now spans additional MIT classes, CERN, Harvard, and internal deployments such as CSAIL's support staff.

### Educational Support

Archi assists TAs, lecturers, and support staff—or students directly—by preparing answers based on curated class resources. In MIT course deployments, Archi leverages Piazza posts, documentation, and other class-specific materials. The Piazza integration can draft answers for staff to review or send, while the system continuously learns from revisions and new posts, improving over time.

### Research Resource Support

Archi also serves technical support teams and end users. At SubMIT, it functions both as a user-facing chatbot and as a ticket assistant. Integration with Redmine enables Archi to prepare draft responses to support tickets that staff can review before sending. In both roles, Archi accesses the corpus of tickets and documentation, citing relevant sources in its answers.

---

## Documentation

| Section | Description |
|---------|-------------|
| [Install](install.md) | System requirements and installation |
| [Quickstart](quickstart.md) | Deploy your first instance in minutes |
| [User Guide](user_guide.md) | Overview of all capabilities |
| [Data Sources](data_sources.md) | Configure web links, git, JIRA, Redmine, and more |
| [Services](services.md) | Chat, uploader, data manager, Piazza, Mattermost, and other interfaces |
| [Models & Providers](models_providers.md) | LLM providers (OpenAI, Anthropic, Gemini, OpenRouter, Local), embeddings, BYOK |
| [Agents & Tools](agents_tools.md) | Agent specs, tools, MCP integration, pipelines |
| [Configuration](configuration.md) | Full YAML config schema reference |
| [CLI Reference](cli_reference.md) | All CLI commands and options |
| [API Reference](api_reference.md) | REST API endpoints |
| [Benchmarking](benchmarking.md) | Evaluate retrieval and response quality |
| [Developer Guide](developer_guide.md) | Architecture, contributing, extending the stack |
| [Advanced Setup](advanced_setup_deploy.md) | GPU setup, multi-node, production deployment |
| [Troubleshooting](troubleshooting.md) | Common issues and fixes |
