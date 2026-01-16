# Uplift Data Manager

## Overview

Extract G5 specs from the data manager module (`src/data_manager/`). This module handles data collection from various sources (web, git, tickets) and manages vector storage for retrieval.

## Goals

1. Extract specs for all data manager components
2. Document the collector architecture and protocols
3. Document the vectorstore and retrieval systems
4. Enable G5 workflow for future data pipeline development

## Non-Goals

- Refactoring existing code
- Adding new data sources
- Changing existing behavior

## Module Structure

```
src/data_manager/
├── __init__.py
├── data_manager.py              # Main DataManager orchestrator
├── collectors/
│   ├── base.py                  # Collector protocol
│   ├── persistence.py           # PersistenceService
│   ├── resource_base.py         # BaseResource
│   ├── utils/
│   │   ├── anonymizer.py        # Data anonymization
│   │   ├── embedding_utils.py   # Embedding helpers
│   │   ├── index_utils.py       # CatalogService
│   │   └── metadata.py          # ResourceMetadata
│   ├── scrapers/
│   │   ├── scraper.py           # LinkScraper
│   │   ├── scraper_manager.py   # ScraperManager
│   │   ├── scraped_resource.py  # ScrapedResource
│   │   └── integrations/
│   │       ├── git_scraper.py   # GitScraper
│   │       └── sso_scraper.py   # SSOScraper
│   └── tickets/
│       ├── ticket_manager.py    # TicketManager
│       ├── ticket_resource.py   # TicketResource
│       └── integrations/
│           ├── redmine_tickets.py
│           └── jira.py
└── vectorstore/
    ├── manager.py               # VectorStoreManager
    ├── loader_utils.py          # Document loaders
    └── retrievers/
        ├── bm25_retriever.py    # BM25LexicalRetriever
        ├── hybrid_retriever.py  # HybridRetriever
        ├── semantic_retriever.py # SemanticRetriever
        ├── grading_retriever.py # GradingRetriever
        └── utils.py             # Retriever utilities
```

## Architecture

### Data Flow

```
Sources (web, git, tickets)
    ↓
Collectors (ScraperManager, TicketManager)
    ↓
PersistenceService (filesystem)
    ↓
VectorStoreManager (ChromaDB)
    ↓
Retrievers (BM25, Semantic, Hybrid)
```

### Key Patterns

1. **Collector Protocol**: All collectors implement `collect(persistence)`
2. **Resource Pattern**: Data wrapped in Resource classes with metadata
3. **Index Management**: CatalogService tracks file hashes
4. **Retriever Hierarchy**: BaseRetriever → specific implementations

## Specs to Create

| Spec | Class(es) | Type |
|------|-----------|------|
| `data-manager/core.spec.md` | `DataManager` | Orchestrator |
| `data-manager/persistence.spec.md` | `PersistenceService`, `CatalogService` | Storage |
| `data-manager/collectors.spec.md` | `Collector`, `BaseResource`, `ResourceMetadata` | Protocol |
| `data-manager/scrapers.spec.md` | `ScraperManager`, `LinkScraper`, `ScrapedResource` | Collector |
| `data-manager/tickets.spec.md` | `TicketManager`, `TicketResource` | Collector |
| `data-manager/vectorstore.spec.md` | `VectorStoreManager` | Storage |
| `data-manager/retrievers.spec.md` | `HybridRetriever`, `BM25Retriever`, `SemanticRetriever` | Retrieval |

## Success Criteria

- [ ] All data manager classes have specs
- [ ] Collector protocol documented
- [ ] Persistence layer documented
- [ ] Retrieval strategies documented
