"""
Text Search Benchmark: PostgreSQL Full-Text Search vs in-memory BM25

Compares:
- Query latency (p50, p95, p99)
- Throughput (queries/second)
- Result quality (if applicable)

For various dataset sizes: 100, 1000, 5000, 10000 documents
"""

import time
import statistics
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import numpy as np
from tqdm import tqdm

# Database clients
import psycopg2
from psycopg2.extras import execute_values

# BM25 implementation
from rank_bm25 import BM25Okapi

from generate_data import DataGenerator


@dataclass
class TextSearchResult:
    """Results from a single benchmark run."""
    backend: str
    num_chunks: int
    num_queries: int
    setup_time_ms: float
    latencies_ms: List[float] = field(default_factory=list)
    
    @property
    def p50(self) -> float:
        return statistics.median(self.latencies_ms) if self.latencies_ms else 0
    
    @property
    def p95(self) -> float:
        if not self.latencies_ms:
            return 0
        sorted_lat = sorted(self.latencies_ms)
        idx = int(len(sorted_lat) * 0.95)
        return sorted_lat[idx]
    
    @property
    def p99(self) -> float:
        if not self.latencies_ms:
            return 0
        sorted_lat = sorted(self.latencies_ms)
        idx = int(len(sorted_lat) * 0.99)
        return sorted_lat[idx]
    
    @property
    def throughput(self) -> float:
        """Queries per second."""
        total_time_sec = sum(self.latencies_ms) / 1000
        return len(self.latencies_ms) / total_time_sec if total_time_sec > 0 else 0
    
    def to_dict(self) -> dict:
        return {
            "backend": self.backend,
            "num_chunks": self.num_chunks,
            "num_queries": self.num_queries,
            "setup_time_ms": round(self.setup_time_ms, 2),
            "p50_ms": round(self.p50, 3),
            "p95_ms": round(self.p95, 3),
            "p99_ms": round(self.p99, 3),
            "throughput_qps": round(self.throughput, 1),
        }


class PostgresTextBenchmark:
    """Benchmark PostgreSQL full-text search."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5433,
        user: str = "benchmark",
        password: str = "benchmark",
        database: str = "benchmark",
    ):
        self.conn_params = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
        }
        self.conn: Optional[psycopg2.extensions.connection] = None
    
    def connect(self):
        """Establish database connection."""
        self.conn = psycopg2.connect(**self.conn_params)
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def reset_table(self):
        """Drop and recreate the chunks table for text search."""
        with self.conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS text_chunks CASCADE")
            cur.execute("""
                CREATE TABLE text_chunks (
                    chunk_id SERIAL PRIMARY KEY,
                    doc_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    chunk_text TEXT NOT NULL,
                    chunk_tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', chunk_text)) STORED
                )
            """)
            self.conn.commit()
    
    def insert_and_index(self, chunks: List[Tuple]) -> float:
        """Insert chunks, build index, and return total time in ms."""
        start = time.perf_counter()
        
        with self.conn.cursor() as cur:
            # Prepare data for bulk insert
            values = [
                (doc_id, chunk_idx, text)
                for doc_id, chunk_idx, text, _, _ in chunks
            ]
            
            execute_values(
                cur,
                """
                INSERT INTO text_chunks (doc_id, chunk_index, chunk_text)
                VALUES %s
                """,
                values,
                page_size=1000,
            )
            
            # Build GIN index on tsvector
            cur.execute("DROP INDEX IF EXISTS idx_text_chunks_tsv")
            cur.execute("CREATE INDEX idx_text_chunks_tsv ON text_chunks USING GIN (chunk_tsv)")
            
            # Analyze for query planner
            cur.execute("ANALYZE text_chunks")
            self.conn.commit()
        
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed
    
    def text_search(self, query: str, top_k: int = 5) -> float:
        """Execute full-text search and return latency in ms."""
        start = time.perf_counter()
        
        with self.conn.cursor() as cur:
            # Use plainto_tsquery for simple query parsing
            # websearch_to_tsquery is more flexible but requires PG 11+
            cur.execute(
                """
                SELECT chunk_id, chunk_text, ts_rank(chunk_tsv, query) as rank
                FROM text_chunks, plainto_tsquery('english', %s) query
                WHERE chunk_tsv @@ query
                ORDER BY rank DESC
                LIMIT %s
                """,
                (query, top_k)
            )
            results = cur.fetchall()
        
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed
    
    def run_benchmark(
        self,
        chunks: List[Tuple],
        queries: List[str],
        top_k: int = 5,
    ) -> TextSearchResult:
        """Run complete benchmark."""
        self.connect()
        
        try:
            # Reset and insert data
            self.reset_table()
            setup_time = self.insert_and_index(chunks)
            
            # Run queries
            latencies = []
            for query in tqdm(queries, desc="PostgreSQL FTS queries"):
                lat = self.text_search(query, top_k)
                latencies.append(lat)
            
            return TextSearchResult(
                backend="postgres_fts",
                num_chunks=len(chunks),
                num_queries=len(queries),
                setup_time_ms=setup_time,
                latencies_ms=latencies,
            )
        finally:
            self.close()


class BM25Benchmark:
    """Benchmark in-memory BM25."""
    
    def __init__(self):
        self.bm25 = None
        self.documents = []
        self.chunk_ids = []
    
    def setup(self, chunks: List[Tuple]) -> float:
        """Build BM25 index and return time in ms."""
        start = time.perf_counter()
        
        # Tokenize documents (simple whitespace tokenization)
        self.documents = []
        self.chunk_ids = []
        tokenized_docs = []
        
        for i, (doc_id, chunk_idx, text, _, _) in enumerate(chunks):
            self.documents.append(text)
            self.chunk_ids.append(i)
            # Simple tokenization: lowercase and split
            tokens = text.lower().split()
            tokenized_docs.append(tokens)
        
        # Build BM25 index
        self.bm25 = BM25Okapi(tokenized_docs)
        
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed
    
    def text_search(self, query: str, top_k: int = 5) -> float:
        """Execute BM25 search and return latency in ms."""
        start = time.perf_counter()
        
        # Tokenize query
        query_tokens = query.lower().split()
        
        # Get scores
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        # Get results
        results = [
            (self.chunk_ids[i], self.documents[i], scores[i])
            for i in top_indices
            if scores[i] > 0
        ]
        
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed
    
    def run_benchmark(
        self,
        chunks: List[Tuple],
        queries: List[str],
        top_k: int = 5,
    ) -> TextSearchResult:
        """Run complete benchmark."""
        # Setup BM25 index
        setup_time = self.setup(chunks)
        
        # Run queries
        latencies = []
        for query in tqdm(queries, desc="BM25 queries"):
            lat = self.text_search(query, top_k)
            latencies.append(lat)
        
        return TextSearchResult(
            backend="bm25_memory",
            num_chunks=len(chunks),
            num_queries=len(queries),
            setup_time_ms=setup_time,
            latencies_ms=latencies,
        )


def generate_text_queries(num_queries: int = 100) -> List[str]:
    """Generate realistic text search queries."""
    import random
    
    templates = [
        "how to configure {topic}",
        "{topic} error troubleshooting",
        "best practices {topic}",
        "{topic} performance optimization",
        "deploy {topic} production",
        "{topic} tutorial guide",
        "debug {topic} issues",
        "{topic} vs alternative",
        "install setup {topic}",
        "{topic} api documentation",
    ]
    
    topics = [
        "database", "api", "server", "model", "function",
        "container", "cluster", "network", "cache", "index",
        "python", "docker", "kubernetes", "machine learning",
        "neural network", "vector", "embedding", "query",
    ]
    
    queries = []
    for _ in range(num_queries):
        template = random.choice(templates)
        topic = random.choice(topics)
        queries.append(template.format(topic=topic))
    
    return queries


def run_text_benchmarks(
    doc_counts: List[int] = [100, 1000, 5000, 10000],
    num_queries: int = 100,
    chunks_per_doc: int = 5,
    top_k: int = 5,
) -> List[TextSearchResult]:
    """Run text search benchmarks for multiple dataset sizes."""
    results = []
    generator = DataGenerator()
    
    # Generate queries once (same queries for all dataset sizes)
    queries = generate_text_queries(num_queries)
    
    for num_docs in doc_counts:
        print(f"\n{'='*60}")
        print(f"Text Search Benchmark: {num_docs} documents (~{num_docs * chunks_per_doc} chunks)")
        print(f"{'='*60}")
        
        # Generate data
        print("Generating synthetic data...")
        chunks = generator.generate_dataset(num_docs, chunks_per_doc)
        
        # Run PostgreSQL FTS benchmark
        print("\nRunning PostgreSQL full-text search benchmark...")
        try:
            pg_bench = PostgresTextBenchmark()
            pg_result = pg_bench.run_benchmark(chunks, queries, top_k)
            results.append(pg_result)
            print(f"  PostgreSQL FTS: p50={pg_result.p50:.2f}ms, p95={pg_result.p95:.2f}ms, throughput={pg_result.throughput:.1f} qps")
        except Exception as e:
            print(f"  PostgreSQL FTS error: {e}")
        
        # Run BM25 benchmark
        print("\nRunning in-memory BM25 benchmark...")
        try:
            bm25_bench = BM25Benchmark()
            bm25_result = bm25_bench.run_benchmark(chunks, queries, top_k)
            results.append(bm25_result)
            print(f"  BM25: p50={bm25_result.p50:.2f}ms, p95={bm25_result.p95:.2f}ms, throughput={bm25_result.throughput:.1f} qps")
        except Exception as e:
            print(f"  BM25 error: {e}")
    
    return results


if __name__ == "__main__":
    print("Text Search Benchmark: PostgreSQL FTS vs BM25")
    print("=" * 60)
    
    # Run with smaller dataset for quick test
    results = run_text_benchmarks(
        doc_counts=[100, 1000],
        num_queries=50,
    )
    
    print("\n\nSummary:")
    print("-" * 80)
    from tabulate import tabulate
    
    table_data = [r.to_dict() for r in results]
    print(tabulate(table_data, headers="keys", tablefmt="grid"))
