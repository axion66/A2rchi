---
type: spec
module: data_manager.collectors
version: "1.0"
status: extracted
test_file: tests/unit/test_collectors.py
source_files:
  - src/data_manager/collectors/base.py
  - src/data_manager/collectors/resource_base.py
  - src/data_manager/collectors/utils/metadata.py
---

# Collectors Base Spec

## Overview

Base protocols and classes for the collector system. Defines the interface for data collection and resource representation.

## Public API

### Protocols

#### `Collector`
```python
class Collector(Protocol):
    """Protocol for classes capable of collecting data into persistence."""
    
    def collect(self, persistence: PersistenceService) -> None:
        """Execute collection and persist results."""
        ...
```

**Contracts:**
- REQUIRES: Valid `PersistenceService` instance
- ENSURES: All collected data persisted via the service

---

### Classes

#### `BaseResource`
```python
class BaseResource(ABC):
    """Abstract representation of a persisted resource."""
```

**Abstract Methods:**

##### `get_hash`
```python
@abstractmethod
def get_hash(self) -> str
```
Return unique identifier for the resource.

##### `get_filename`
```python
@abstractmethod
def get_filename(self) -> str
```
Return filename (with extension) for persistence.

##### `get_content`
```python
@abstractmethod
def get_content(self) -> Union[str, bytes, bytearray]
```
Return content to be persisted.

**Concrete Methods:**

##### `get_file_path`
```python
def get_file_path(self, target_dir: Path) -> Path
```
Return full path: `target_dir / get_filename()`.

##### `get_metadata_path`
```python
def get_metadata_path(self, file_path: Path) -> Optional[Path]
```
Return metadata path or None.

**Contracts:**
- ENSURES: Metadata path is `{file_path}.meta.yaml` if metadata exists

##### `get_metadata`
```python
def get_metadata(self) -> Optional[ResourceMetadata]
```
Return metadata object or None. Default returns None.

---

#### `ResourceMetadata`
```python
@dataclass
class ResourceMetadata:
    """Metadata describing a collected resource."""
    
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    collected_at: Optional[datetime] = None
    title: Optional[str] = None
    author: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)
```

**Methods:**

##### `to_dict`
```python
def to_dict(self) -> Dict[str, Any]
```
Convert to dictionary for YAML serialization.

##### `from_dict`
```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> ResourceMetadata
```
Create from dictionary.

## Resource Lifecycle

```
1. Collector creates Resource with content and metadata
2. Resource.get_hash() provides unique identifier
3. Resource.get_content() provides data to write
4. Resource.get_metadata() provides optional metadata
5. PersistenceService writes both to disk
6. Index updated with hash → path mapping
```

## Invariants

1. Hash must be deterministic for same content
2. Filename must be filesystem-safe
3. Content can be text or binary
4. Metadata is always optional
