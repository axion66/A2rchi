# PostgreSQL Migration Benchmarks

Performance comparison benchmarks for the PostgreSQL consolidation migration:
1. **Vector Search**: pgvector vs ChromaDB
2. **Text Search**: PostgreSQL full-text search vs in-memory BM25

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL with pgvector (Docker)
docker compose up -d

# Run all benchmarks
python run_benchmarks.py

# Run specific benchmark
python run_benchmarks.py --vector-only
python run_benchmarks.py --text-only
```

## Benchmark Parameters

- **Document counts**: 100, 1,000, 5,000, 10,000
- **Embedding dimensions**: 1536 (OpenAI ada-002 compatible)
- **Query iterations**: 100 per configuration
- **Metrics**: p50, p95, p99 latency, throughput (queries/sec)

## Success Criteria

From the proposal:
- Latency within **2x** of current solution for datasets up to 10K documents
- Memory usage should not exceed current baseline significantly

## Files

- `docker-compose.yml` - PostgreSQL + pgvector setup
- `Dockerfile.postgres` - Custom postgres image with pgvector
- `init.sql` - Schema with vector and fulltext indexes
- `generate_data.py` - Synthetic document/embedding generator
- `benchmark_vector.py` - pgvector vs ChromaDB comparison
- `benchmark_text.py` - PostgreSQL FTS vs BM25 comparison
- `run_benchmarks.py` - Main benchmark runner
- `requirements.txt` - Python dependencies
