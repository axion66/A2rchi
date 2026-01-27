"""
Vector Search Benchmark: pgvector vs ChromaDB

Compares:
- Query latency (p50, p95, p99)
- Throughput (queries/second)
- Memory usage
- Index build time

For various dataset sizes: 100, 1000, 5000, 10000 documents
"""

import json
import time
import statistics
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import numpy as np
from tqdm import tqdm

# Database clients
import psycopg2
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector
import chromadb

from generate_data import DataGenerator


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    backend: str
    num_chunks: int
    num_queries: int
    index_build_time_ms: float
    insert_time_ms: float
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
            "index_build_time_ms": round(self.index_build_time_ms, 2),
            "insert_time_ms": round(self.insert_time_ms, 2),
            "p50_ms": round(self.p50, 3),
            "p95_ms": round(self.p95, 3),
            "p99_ms": round(self.p99, 3),
            "throughput_qps": round(self.throughput, 1),
        }


class PostgresBenchmark:
    """Benchmark pgvector in PostgreSQL."""
    
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
        register_vector(self.conn)
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def reset_table(self):
        """Drop and recreate the chunks table."""
        with self.conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS document_chunks CASCADE")
            cur.execute("""
                CREATE TABLE document_chunks (
                    chunk_id SERIAL PRIMARY KEY,
                    doc_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    chunk_text TEXT NOT NULL,
                    embedding vector(1536),
                    metadata JSONB DEFAULT '{}',
                    chunk_tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', chunk_text)) STORED,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            self.conn.commit()
    
    def insert_chunks(self, chunks: List[Tuple]) -> float:
        """Insert chunks and return time in ms."""
        start = time.perf_counter()
        
        with self.conn.cursor() as cur:
            # Prepare data for bulk insert
            values = [
                (doc_id, chunk_idx, text, embedding.tolist(), json.dumps(metadata))
                for doc_id, chunk_idx, text, embedding, metadata in chunks
            ]
            
            execute_values(
                cur,
                """
                INSERT INTO document_chunks (doc_id, chunk_index, chunk_text, embedding, metadata)
                VALUES %s
                """,
                values,
                template="(%s, %s, %s, %s::vector, %s::jsonb)",
                page_size=1000,
            )
            self.conn.commit()
        
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed
    
    def build_index(self) -> float:
        """Build HNSW index and return time in ms."""
        start = time.perf_counter()
        
        with self.conn.cursor() as cur:
            # Drop existing index if any
            cur.execute("DROP INDEX IF EXISTS idx_chunks_embedding_hnsw")
            # Build HNSW index
            cur.execute("""
                CREATE INDEX idx_chunks_embedding_hnsw ON document_chunks 
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            """)
            # Also create fulltext index
            cur.execute("DROP INDEX IF EXISTS idx_chunks_fulltext")
            cur.execute("CREATE INDEX idx_chunks_fulltext ON document_chunks USING GIN (chunk_tsv)")
            # Analyze for query planner
            cur.execute("ANALYZE document_chunks")
            self.conn.commit()
        
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed
    
    def vector_search(self, embedding: np.ndarray, top_k: int = 5) -> float:
        """Execute vector search and return latency in ms."""
        start = time.perf_counter()
        
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT chunk_id, chunk_text, 1 - (embedding <=> %s::vector) as similarity
                FROM document_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (embedding.tolist(), embedding.tolist(), top_k)
            )
            results = cur.fetchall()
        
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed
    
    def run_benchmark(
        self,
        chunks: List[Tuple],
        queries: List[Tuple[str, np.ndarray]],
        top_k: int = 5,
    ) -> BenchmarkResult:
        """Run complete benchmark."""
        self.connect()
        
        try:
            # Reset and insert data
            self.reset_table()
            insert_time = self.insert_chunks(chunks)
            
            # Build index
            index_time = self.build_index()
            
            # Run queries
            latencies = []
            for query_text, query_embedding in tqdm(queries, desc="pgvector queries"):
                lat = self.vector_search(query_embedding, top_k)
                latencies.append(lat)
            
            return BenchmarkResult(
                backend="pgvector",
                num_chunks=len(chunks),
                num_queries=len(queries),
                index_build_time_ms=index_time,
                insert_time_ms=insert_time,
                latencies_ms=latencies,
            )
        finally:
            self.close()


class ChromaDBBenchmark:
    """Benchmark ChromaDB."""
    
    def __init__(self, persist_directory: str = "./.chroma_benchmark"):
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
    
    def connect(self):
        """Initialize ChromaDB client."""
        # Use the new ChromaDB API (v0.4+)
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
        )
    
    def close(self):
        """Close client (persist if needed)."""
        if self.client:
            self.client = None
            self.collection = None
    
    def reset_collection(self):
        """Delete and recreate collection."""
        try:
            self.client.delete_collection("benchmark")
        except Exception:
            pass
        self.collection = self.client.create_collection(
            name="benchmark",
            metadata={"hnsw:space": "cosine"},
        )
    
    def insert_chunks(self, chunks: List[Tuple]) -> float:
        """Insert chunks and return time in ms."""
        start = time.perf_counter()
        
        # Prepare data for ChromaDB
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for i, (doc_id, chunk_idx, text, embedding, metadata) in enumerate(chunks):
            ids.append(f"chunk_{i}")
            embeddings.append(embedding.tolist())
            documents.append(text)
            metadatas.append(metadata)
        
        # ChromaDB has batch size limits, insert in batches
        batch_size = 5000
        for i in range(0, len(ids), batch_size):
            end = min(i + batch_size, len(ids))
            self.collection.add(
                ids=ids[i:end],
                embeddings=embeddings[i:end],
                documents=documents[i:end],
                metadatas=metadatas[i:end],
            )
        
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed
    
    def vector_search(self, embedding: np.ndarray, top_k: int = 5) -> float:
        """Execute vector search and return latency in ms."""
        start = time.perf_counter()
        
        results = self.collection.query(
            query_embeddings=[embedding.tolist()],
            n_results=top_k,
        )
        
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed
    
    def run_benchmark(
        self,
        chunks: List[Tuple],
        queries: List[Tuple[str, np.ndarray]],
        top_k: int = 5,
    ) -> BenchmarkResult:
        """Run complete benchmark."""
        self.connect()
        
        try:
            # Reset and insert data
            self.reset_collection()
            insert_time = self.insert_chunks(chunks)
            
            # ChromaDB builds index automatically during insert
            # We'll measure a dummy "index" time as 0
            index_time = 0.0
            
            # Run queries
            latencies = []
            for query_text, query_embedding in tqdm(queries, desc="ChromaDB queries"):
                lat = self.vector_search(query_embedding, top_k)
                latencies.append(lat)
            
            return BenchmarkResult(
                backend="chromadb",
                num_chunks=len(chunks),
                num_queries=len(queries),
                index_build_time_ms=index_time,
                insert_time_ms=insert_time,
                latencies_ms=latencies,
            )
        finally:
            self.close()


def run_vector_benchmarks(
    doc_counts: List[int] = [100, 1000, 5000, 10000],
    num_queries: int = 100,
    chunks_per_doc: int = 5,
    top_k: int = 5,
) -> List[BenchmarkResult]:
    """Run vector search benchmarks for multiple dataset sizes."""
    results = []
    generator = DataGenerator()
    
    for num_docs in doc_counts:
        print(f"\n{'='*60}")
        print(f"Benchmarking with {num_docs} documents (~{num_docs * chunks_per_doc} chunks)")
        print(f"{'='*60}")
        
        # Generate data
        print("Generating synthetic data...")
        chunks = generator.generate_dataset(num_docs, chunks_per_doc)
        queries = generator.generate_queries(num_queries)
        
        # Run pgvector benchmark
        print("\nRunning pgvector benchmark...")
        try:
            pg_bench = PostgresBenchmark()
            pg_result = pg_bench.run_benchmark(chunks, queries, top_k)
            results.append(pg_result)
            print(f"  pgvector: p50={pg_result.p50:.2f}ms, p95={pg_result.p95:.2f}ms, throughput={pg_result.throughput:.1f} qps")
        except Exception as e:
            print(f"  pgvector error: {e}")
        
        # Run ChromaDB benchmark
        print("\nRunning ChromaDB benchmark...")
        try:
            chroma_bench = ChromaDBBenchmark()
            chroma_result = chroma_bench.run_benchmark(chunks, queries, top_k)
            results.append(chroma_result)
            print(f"  ChromaDB: p50={chroma_result.p50:.2f}ms, p95={chroma_result.p95:.2f}ms, throughput={chroma_result.throughput:.1f} qps")
        except Exception as e:
            print(f"  ChromaDB error: {e}")
    
    return results


if __name__ == "__main__":
    print("Vector Search Benchmark: pgvector vs ChromaDB")
    print("=" * 60)
    
    # Run with smaller dataset for quick test
    results = run_vector_benchmarks(
        doc_counts=[100, 1000],
        num_queries=50,
    )
    
    print("\n\nSummary:")
    print("-" * 80)
    from tabulate import tabulate
    
    table_data = [r.to_dict() for r in results]
    print(tabulate(table_data, headers="keys", tablefmt="grid"))
