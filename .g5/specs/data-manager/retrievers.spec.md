---
type: spec
module: data_manager.vectorstore.retrievers
version: "1.0"
status: extracted
test_file: tests/unit/test_retrievers.py
source_files:
  - src/data_manager/vectorstore/retrievers/hybrid_retriever.py
  - src/data_manager/vectorstore/retrievers/bm25_retriever.py
  - src/data_manager/vectorstore/retrievers/semantic_retriever.py
---

# Retrievers Spec

## Overview

Document retrieval implementations including lexical (BM25), semantic (embedding), and hybrid (combined) approaches.

## Dependencies

- `langchain_core.retrievers.BaseRetriever`
- `langchain_community.retrievers.BM25Retriever`
- `langchain_classic.retrievers.EnsembleRetriever`
- `langchain_core.vectorstores.base.VectorStore`

## Public API

### Classes

#### `SemanticRetriever`
```python
class SemanticRetriever(BaseRetriever):
    """Retriever using embedding similarity search."""
    
    vectorstore: VectorStore
    k: int = 3
    instructions: Optional[str] = None
    dm_config: Dict
```

**Constructor:**
```python
def __init__(self, vectorstore: VectorStore, dm_config: Dict, k: int = 3, instructions: str = None)
```

**Methods:**

##### `_get_relevant_documents`
```python
def _get_relevant_documents(self, query: str) -> List[Tuple[Document, float]]
```
Retrieve documents using vector similarity.

**Contracts:**
- ENSURES: Uses `vectorstore.similarity_search_with_score()`
- ENSURES: Adds instructions to query if model supports it
- ENSURES: Returns list of `(Document, score)` tuples

---

#### `BM25LexicalRetriever`
```python
class BM25LexicalRetriever(BaseRetriever):
    """BM25 lexical retriever built from vectorstore corpus."""
    
    vectorstore: VectorStore
    k: int
    bm25_k1: float = 0.5
    bm25_b: float = 0.75
    _bm25_retriever: Optional[LangChainBM25Retriever]
```

**Constructor:**
```python
def __init__(self, vectorstore: VectorStore, k: int = 3, bm25_k1: float = 0.5, bm25_b: float = 0.75)
```

**Contracts:**
- ENSURES: Loads all documents from vectorstore
- ENSURES: Initializes LangChain BM25Retriever

**Properties:**

##### `ready`
```python
@property
def ready(self) -> bool
```
True when underlying retriever initialized.

**Methods:**

##### `_get_relevant_documents`
```python
def _get_relevant_documents(self, query: str, *, run_manager=None) -> List[Document]
```
Retrieve using BM25 algorithm.

##### `_get_all_documents_from_vectorstore`
```python
def _get_all_documents_from_vectorstore(self) -> List[Document]
```
Extract all documents for BM25 corpus.

**Contracts:**
- ENSURES: Accesses ChromaDB collection directly
- ENSURES: Reconstructs Document objects from stored data

---

#### `HybridRetriever`
```python
class HybridRetriever(BaseRetriever):
    """Combines BM25 (lexical) and semantic search."""
    
    vectorstore: VectorStore
    k: int
    bm25_weight: float = 0.6
    semantic_weight: float = 0.4
    bm25_k1: float = 0.5
    bm25_b: float = 0.75
    _bm25_retriever: BM25LexicalRetriever
    _ensemble_retriever: EnsembleRetriever
```

**Constructor:**
```python
def __init__(self, vectorstore: VectorStore, k: int = 3,
             bm25_weight: float = 0.6, semantic_weight: float = 0.4,
             bm25_k1: float = 0.5, bm25_b: float = 0.75)
```

**Contracts:**
- ENSURES: Initializes `BM25LexicalRetriever`
- ENSURES: Creates dense retriever from vectorstore
- ENSURES: Combines with `EnsembleRetriever`

**Methods:**

##### `_get_relevant_documents`
```python
def _get_relevant_documents(self, query: str, *, run_manager=None) -> List[Tuple[Document, float]]
```
Retrieve using hybrid search.

**Contracts:**
- REQUIRES: `_ensemble_retriever` initialized
- ENSURES: Returns documents with placeholder scores (-1.0)

##### `_compute_hybrid_scores`
```python
def _compute_hybrid_scores(self, docs: List[Document], query: str) -> List[Tuple[Document, float]]
```
Assign scores to hybrid results.

**Contracts:**
- ENSURES: Returns -1.0 placeholder scores (not yet calibrated)

## Retriever Comparison

| Retriever | Method | Scores | Use Case |
|-----------|--------|--------|----------|
| SemanticRetriever | Embedding similarity | Actual scores | Dense retrieval |
| BM25LexicalRetriever | BM25 term matching | N/A | Keyword matching |
| HybridRetriever | Ensemble (BM25 + semantic) | Placeholder (-1) | Best of both |

## Configuration

Used via pipelines:
```yaml
data_manager:
  retrievers:
    hybrid_retriever:
      num_documents_to_retrieve: 5
      bm25_weight: 0.6
      semantic_weight: 0.4
    bm25_retriever:
      k1: 0.5
      b: 0.75
    semantic_retriever:
      num_documents_to_retrieve: 5
```

## Invariants

1. BM25 requires loading all documents upfront
2. Hybrid scores are placeholders until calibration
3. All retrievers return documents in relevance order
4. k determines number of results
