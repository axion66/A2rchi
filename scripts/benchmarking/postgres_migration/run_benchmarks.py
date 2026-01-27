#!/usr/bin/env python3
"""
PostgreSQL Migration Benchmark Runner

Runs all benchmarks and generates a summary report.

Usage:
    python run_benchmarks.py              # Run all benchmarks
    python run_benchmarks.py --vector     # Vector search only
    python run_benchmarks.py --text       # Text search only
    python run_benchmarks.py --quick      # Quick test (small datasets)
    python run_benchmarks.py --full       # Full benchmark suite
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from tabulate import tabulate


def check_postgres_running() -> bool:
    """Check if PostgreSQL container is running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=a2rchi-postgres-benchmark", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
        )
        return "a2rchi-postgres-benchmark" in result.stdout
    except Exception:
        return False


def start_postgres():
    """Start PostgreSQL container."""
    script_dir = Path(__file__).parent
    print("Starting PostgreSQL with pgvector...")
    subprocess.run(
        ["docker", "compose", "up", "-d", "--build"],
        cwd=script_dir,
        check=True,
    )
    
    # Wait for PostgreSQL to be ready
    print("Waiting for PostgreSQL to be ready...")
    for i in range(30):
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                port=5433,
                user="benchmark",
                password="benchmark",
                database="benchmark",
            )
            conn.close()
            print("PostgreSQL is ready!")
            return
        except Exception:
            time.sleep(1)
    
    raise RuntimeError("PostgreSQL failed to start within 30 seconds")


def stop_postgres():
    """Stop PostgreSQL container."""
    script_dir = Path(__file__).parent
    print("Stopping PostgreSQL...")
    subprocess.run(
        ["docker", "compose", "down"],
        cwd=script_dir,
    )


def run_vector_benchmarks(doc_counts: list, num_queries: int) -> list:
    """Run vector search benchmarks."""
    from benchmark_vector import run_vector_benchmarks as _run
    return _run(doc_counts=doc_counts, num_queries=num_queries)


def run_text_benchmarks(doc_counts: list, num_queries: int) -> list:
    """Run text search benchmarks."""
    from benchmark_text import run_text_benchmarks as _run
    return _run(doc_counts=doc_counts, num_queries=num_queries)


def generate_report(vector_results: list, text_results: list, output_dir: Path):
    """Generate benchmark report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"benchmark_report_{timestamp}.md"
    json_path = output_dir / f"benchmark_results_{timestamp}.json"
    
    # Save raw results as JSON
    all_results = {
        "timestamp": timestamp,
        "vector_benchmarks": [r.to_dict() for r in vector_results] if vector_results else [],
        "text_benchmarks": [r.to_dict() for r in text_results] if text_results else [],
    }
    
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2)
    
    # Generate markdown report
    report_lines = [
        "# PostgreSQL Migration Benchmark Report",
        f"\nGenerated: {datetime.now().isoformat()}",
        "\n## Success Criteria",
        "- Latency within **2x** of current solution for datasets up to 10K documents",
        "\n---\n",
    ]
    
    if vector_results:
        report_lines.append("## Vector Search: pgvector vs ChromaDB\n")
        
        # Group by num_chunks
        chunks_to_results = {}
        for r in vector_results:
            key = r.num_chunks
            if key not in chunks_to_results:
                chunks_to_results[key] = {}
            chunks_to_results[key][r.backend] = r
        
        # Create comparison table
        comparison_data = []
        for num_chunks in sorted(chunks_to_results.keys()):
            results = chunks_to_results[num_chunks]
            pg = results.get("pgvector")
            chroma = results.get("chromadb")
            
            if pg and chroma:
                ratio = pg.p50 / chroma.p50 if chroma.p50 > 0 else 0
                status = "✅" if ratio <= 2.0 else "⚠️"
                comparison_data.append({
                    "chunks": num_chunks,
                    "pgvector_p50": f"{pg.p50:.2f}ms",
                    "chromadb_p50": f"{chroma.p50:.2f}ms",
                    "ratio": f"{ratio:.2f}x",
                    "status": status,
                    "pgvector_qps": f"{pg.throughput:.0f}",
                    "chromadb_qps": f"{chroma.throughput:.0f}",
                })
        
        report_lines.append(tabulate(comparison_data, headers="keys", tablefmt="pipe"))
        report_lines.append("\n")
        
        # Full results table
        report_lines.append("\n### Detailed Results\n")
        table_data = [r.to_dict() for r in vector_results]
        report_lines.append(tabulate(table_data, headers="keys", tablefmt="pipe"))
        report_lines.append("\n")
    
    if text_results:
        report_lines.append("\n## Text Search: PostgreSQL FTS vs BM25\n")
        
        # Group by num_chunks
        chunks_to_results = {}
        for r in text_results:
            key = r.num_chunks
            if key not in chunks_to_results:
                chunks_to_results[key] = {}
            chunks_to_results[key][r.backend] = r
        
        # Create comparison table
        comparison_data = []
        for num_chunks in sorted(chunks_to_results.keys()):
            results = chunks_to_results[num_chunks]
            pg = results.get("postgres_fts")
            bm25 = results.get("bm25_memory")
            
            if pg and bm25:
                ratio = pg.p50 / bm25.p50 if bm25.p50 > 0 else 0
                status = "✅" if ratio <= 2.0 else "⚠️"
                comparison_data.append({
                    "chunks": num_chunks,
                    "postgres_fts_p50": f"{pg.p50:.2f}ms",
                    "bm25_p50": f"{bm25.p50:.2f}ms",
                    "ratio": f"{ratio:.2f}x",
                    "status": status,
                    "postgres_fts_qps": f"{pg.throughput:.0f}",
                    "bm25_qps": f"{bm25.throughput:.0f}",
                })
        
        report_lines.append(tabulate(comparison_data, headers="keys", tablefmt="pipe"))
        report_lines.append("\n")
        
        # Full results table
        report_lines.append("\n### Detailed Results\n")
        table_data = [r.to_dict() for r in text_results]
        report_lines.append(tabulate(table_data, headers="keys", tablefmt="pipe"))
        report_lines.append("\n")
    
    # Summary
    report_lines.append("\n## Summary\n")
    
    all_pass = True
    if vector_results:
        pg_results = [r for r in vector_results if r.backend == "pgvector"]
        chroma_results = [r for r in vector_results if r.backend == "chromadb"]
        
        for pg in pg_results:
            chroma = next((c for c in chroma_results if c.num_chunks == pg.num_chunks), None)
            if chroma and pg.p50 / chroma.p50 > 2.0:
                all_pass = False
                report_lines.append(f"- ⚠️ pgvector is >{2}x slower than ChromaDB at {pg.num_chunks} chunks")
    
    if text_results:
        pg_results = [r for r in text_results if r.backend == "postgres_fts"]
        bm25_results = [r for r in text_results if r.backend == "bm25_memory"]
        
        for pg in pg_results:
            bm25 = next((b for b in bm25_results if b.num_chunks == pg.num_chunks), None)
            if bm25 and pg.p50 / bm25.p50 > 2.0:
                all_pass = False
                report_lines.append(f"- ⚠️ PostgreSQL FTS is >{2}x slower than BM25 at {pg.num_chunks} chunks")
    
    if all_pass:
        report_lines.append("- ✅ All benchmarks pass the 2x latency criteria!")
    
    report_lines.append("\n")
    
    # Write report
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))
    
    print(f"\nReport saved to: {report_path}")
    print(f"Raw results saved to: {json_path}")
    
    return report_path


def main():
    parser = argparse.ArgumentParser(description="Run PostgreSQL migration benchmarks")
    parser.add_argument("--vector", action="store_true", help="Run vector search benchmarks only")
    parser.add_argument("--text", action="store_true", help="Run text search benchmarks only")
    parser.add_argument("--quick", action="store_true", help="Quick test with small datasets (100, 500 docs)")
    parser.add_argument("--full", action="store_true", help="Full benchmark (100, 1000, 5000, 10000 docs)")
    parser.add_argument("--no-docker", action="store_true", help="Skip Docker container management")
    parser.add_argument("--queries", type=int, default=100, help="Number of queries to run")
    
    args = parser.parse_args()
    
    # Determine what to run
    run_vector = args.vector or (not args.vector and not args.text)
    run_text = args.text or (not args.vector and not args.text)
    
    # Determine dataset sizes
    if args.quick:
        doc_counts = [100, 500]
        num_queries = 50
    elif args.full:
        doc_counts = [100, 1000, 5000, 10000]
        num_queries = args.queries
    else:
        # Default: medium benchmark
        doc_counts = [100, 1000, 2000]
        num_queries = args.queries
    
    print("=" * 70)
    print("PostgreSQL Migration Benchmarks")
    print("=" * 70)
    print(f"Document counts: {doc_counts}")
    print(f"Queries per test: {num_queries}")
    print(f"Running: {'vector' if run_vector else ''} {'text' if run_text else ''}")
    print("=" * 70)
    
    script_dir = Path(__file__).parent
    
    # Start PostgreSQL if needed
    if not args.no_docker:
        if not check_postgres_running():
            start_postgres()
        else:
            print("PostgreSQL is already running")
    
    vector_results = []
    text_results = []
    
    try:
        if run_vector:
            print("\n" + "=" * 70)
            print("VECTOR SEARCH BENCHMARKS")
            print("=" * 70)
            vector_results = run_vector_benchmarks(doc_counts, num_queries)
        
        if run_text:
            print("\n" + "=" * 70)
            print("TEXT SEARCH BENCHMARKS")
            print("=" * 70)
            text_results = run_text_benchmarks(doc_counts, num_queries)
        
        # Generate report
        generate_report(vector_results, text_results, script_dir)
        
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
    except Exception as e:
        print(f"\nBenchmark failed: {e}")
        raise
    finally:
        # Optionally stop PostgreSQL
        # (Leave it running for debugging)
        pass


if __name__ == "__main__":
    main()
