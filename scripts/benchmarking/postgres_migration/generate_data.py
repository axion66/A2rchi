"""
Synthetic data generator for PostgreSQL migration benchmarks.

Generates realistic document chunks with:
- Random but reproducible embeddings (1536 dimensions)
- Realistic text content using lorem ipsum style generation
- Configurable document and chunk counts
"""

import numpy as np
from typing import Iterator, Tuple, List
import random

# Seed for reproducibility
RANDOM_SEED = 42

# Vocabulary for generating realistic-ish text
WORDS = [
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "I",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
    "people", "into", "year", "your", "good", "some", "could", "them", "see", "other",
    "than", "then", "now", "look", "only", "come", "its", "over", "think", "also",
    "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
    "even", "new", "want", "because", "any", "these", "give", "day", "most", "us",
    # Technical terms for more realistic content
    "system", "data", "process", "function", "method", "class", "object", "value",
    "array", "list", "string", "number", "type", "error", "request", "response",
    "server", "client", "database", "query", "index", "table", "column", "row",
    "user", "admin", "config", "setting", "option", "parameter", "argument", "return",
    "import", "export", "create", "update", "delete", "read", "write", "execute",
    "machine", "learning", "model", "training", "inference", "vector", "embedding",
    "neural", "network", "layer", "weight", "bias", "activation", "gradient", "loss",
    "python", "javascript", "typescript", "rust", "golang", "java", "csharp", "ruby",
    "api", "rest", "graphql", "http", "https", "websocket", "tcp", "udp", "protocol",
    "docker", "kubernetes", "container", "pod", "service", "deployment", "cluster",
]

# Query-like phrases for search benchmarks
QUERY_TEMPLATES = [
    "how to {verb} {noun}",
    "what is {noun}",
    "explain {noun} {noun}",
    "{verb} {noun} in python",
    "best practices for {noun}",
    "troubleshooting {noun} errors",
    "{noun} vs {noun}",
    "configure {noun} settings",
    "optimize {noun} performance",
    "{noun} tutorial guide",
]

VERBS = ["create", "update", "delete", "configure", "optimize", "debug", "deploy", "test", "build", "run"]
NOUNS = ["database", "api", "server", "model", "function", "container", "cluster", "network", "cache", "index"]


def set_seed(seed: int = RANDOM_SEED):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)


def generate_text(min_words: int = 50, max_words: int = 200) -> str:
    """Generate random text content."""
    num_words = random.randint(min_words, max_words)
    words = random.choices(WORDS, k=num_words)
    
    # Add some structure (capitalize first word, add periods)
    text_parts = []
    sentence_words = []
    for i, word in enumerate(words):
        if i == 0 or (sentence_words and random.random() < 0.1):
            if sentence_words:
                sentence_words[-1] += "."
                text_parts.append(" ".join(sentence_words))
                sentence_words = []
            word = word.capitalize()
        sentence_words.append(word)
    
    if sentence_words:
        sentence_words[-1] += "."
        text_parts.append(" ".join(sentence_words))
    
    return " ".join(text_parts)


def generate_embedding(dimensions: int = 1536) -> np.ndarray:
    """Generate a random normalized embedding vector."""
    vec = np.random.randn(dimensions).astype(np.float32)
    # Normalize to unit length (important for cosine similarity)
    vec = vec / np.linalg.norm(vec)
    return vec


def generate_query_embedding(dimensions: int = 1536) -> Tuple[str, np.ndarray]:
    """Generate a query with corresponding embedding."""
    template = random.choice(QUERY_TEMPLATES)
    query = template.format(
        verb=random.choice(VERBS),
        noun=random.choice(NOUNS)
    )
    embedding = generate_embedding(dimensions)
    return query, embedding


def generate_chunks(
    num_documents: int,
    chunks_per_doc: int = 5,
    embedding_dim: int = 1536,
    min_words: int = 50,
    max_words: int = 200,
) -> Iterator[Tuple[int, int, str, np.ndarray, dict]]:
    """
    Generate synthetic document chunks.
    
    Yields:
        Tuple of (doc_id, chunk_index, chunk_text, embedding, metadata)
    """
    for doc_id in range(1, num_documents + 1):
        # Vary chunks per document slightly
        actual_chunks = chunks_per_doc + random.randint(-2, 2)
        actual_chunks = max(1, actual_chunks)
        
        for chunk_idx in range(actual_chunks):
            text = generate_text(min_words, max_words)
            embedding = generate_embedding(embedding_dim)
            metadata = {
                "doc_id": doc_id,
                "chunk_index": chunk_idx,
                "source": f"synthetic_doc_{doc_id}.txt",
                "word_count": len(text.split()),
            }
            yield doc_id, chunk_idx, text, embedding, metadata


def generate_queries(num_queries: int, embedding_dim: int = 1536) -> List[Tuple[str, np.ndarray]]:
    """Generate a batch of search queries with embeddings."""
    return [generate_query_embedding(embedding_dim) for _ in range(num_queries)]


class DataGenerator:
    """Convenient wrapper for generating benchmark data."""
    
    def __init__(self, seed: int = RANDOM_SEED, embedding_dim: int = 1536):
        self.seed = seed
        self.embedding_dim = embedding_dim
        set_seed(seed)
    
    def generate_dataset(
        self,
        num_documents: int,
        chunks_per_doc: int = 5,
    ) -> List[Tuple[int, int, str, np.ndarray, dict]]:
        """Generate a complete dataset as a list."""
        set_seed(self.seed)  # Reset for reproducibility
        return list(generate_chunks(
            num_documents=num_documents,
            chunks_per_doc=chunks_per_doc,
            embedding_dim=self.embedding_dim,
        ))
    
    def generate_queries(self, num_queries: int) -> List[Tuple[str, np.ndarray]]:
        """Generate search queries."""
        # Use different seed offset for queries
        set_seed(self.seed + 1000)
        return generate_queries(num_queries, self.embedding_dim)
    
    def dataset_stats(self, dataset: List) -> dict:
        """Get statistics about a generated dataset."""
        total_words = sum(len(chunk[2].split()) for chunk in dataset)
        return {
            "total_chunks": len(dataset),
            "total_words": total_words,
            "avg_words_per_chunk": total_words / len(dataset) if dataset else 0,
            "embedding_dim": self.embedding_dim,
        }


if __name__ == "__main__":
    # Quick test
    gen = DataGenerator()
    
    print("Generating sample dataset...")
    dataset = gen.generate_dataset(num_documents=10, chunks_per_doc=3)
    stats = gen.dataset_stats(dataset)
    
    print(f"Generated {stats['total_chunks']} chunks")
    print(f"Total words: {stats['total_words']}")
    print(f"Avg words/chunk: {stats['avg_words_per_chunk']:.1f}")
    
    print("\nSample chunk:")
    doc_id, chunk_idx, text, embedding, metadata = dataset[0]
    print(f"  doc_id: {doc_id}, chunk_idx: {chunk_idx}")
    print(f"  text: {text[:100]}...")
    print(f"  embedding shape: {embedding.shape}")
    print(f"  metadata: {metadata}")
    
    print("\nGenerating sample queries...")
    queries = gen.generate_queries(5)
    for query, emb in queries[:3]:
        print(f"  Query: {query}")
