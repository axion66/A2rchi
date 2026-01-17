---
spec_id: data-manager
type: module
status: extracted
children:
  - data-manager/core
  - data-manager/persistence
  - data-manager/collectors
  - data-manager/scrapers
  - data-manager/tickets
  - data-manager/vectorstore
  - data-manager/retrievers
---

# Data Manager Module

Document collection, persistence, and vectorstore management for A2rchi RAG.

## Exports

```python
from src.data_manager import DataManager
from src.data_manager.collectors import PersistenceService, ScraperManager, TicketManager
from src.data_manager.vectorstore import VectorstoreManager
```

## Architecture

```
DataManager (coordinator)
    │
    ├── collectors/           # Data ingestion
    │   ├── PersistenceService   # File I/O + indexing
    │   ├── ScraperManager       # Web scraping
    │   │   └── LinkScraper
    │   └── TicketManager        # Ticket systems
    │       └── TicketResource
    │
    └── vectorstore/          # Vector search
        ├── VectorstoreManager   # Lifecycle management
        └── retrievers/
            └── MultiQueryRetriever
```

## Data Flow

```
Sources (URLs, tickets, files)
         │
         ▼
┌─────────────────┐
│   Collectors    │  ScraperManager, TicketManager
└────────┬────────┘
         │ BaseResource objects
         ▼
┌─────────────────┐
│ Persistence     │  Save to disk + index
│   Service       │
└────────┬────────┘
         │ File paths
         ▼
┌─────────────────┐
│  Vectorstore    │  Embed + store vectors
│   Manager       │
└────────┬────────┘
         │
         ▼
    Retriever (query time)
```

## Resource Protocol

All collected data implements `BaseResource`:

```python
class BaseResource(ABC):
    def get_hash(self) -> str          # Unique ID
    def get_filename(self) -> str      # Filename for persistence
    def get_content(self) -> str|bytes # Data to store
    def get_metadata(self) -> Optional[ResourceMetadata]
```

## Configuration

```yaml
data_manager:
  data_path: "/data"
  sources:
    links:
      enabled: true
      input_lists: ["urls.list"]
    tickets:
      redmine: { enabled: true, ... }
  vectorstore:
    type: "chroma"
    embedding_model: "text-embedding-3-small"
```
