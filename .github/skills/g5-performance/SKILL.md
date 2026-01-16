---
name: g5-performance
description: Guide for performance testing and optimization. Use when dealing with performance issues, profiling code, optimizing algorithms, or adding performance requirements to specs.
---

# G5 Performance

This skill guides you through performance testing and optimization.

## When to Use This Skill

- User reports slowness
- Identified O(n²) or worse algorithms
- Processing large data sets
- Need to add performance requirements to specs
- Profiling to find bottlenecks

## Performance in G5 Context

Performance requirements should be in specs:

```markdown
## Guardrails

- `search()` must complete in O(log n) time
- Memory usage must not exceed 100MB for 10K items
- API response time < 200ms for 95th percentile
```

## Profiling Tools

### Python

```python
# cProfile - function-level profiling
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# ... code to profile ...
profiler.disable()

stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

```bash
# Command line
python -m cProfile -s cumulative script.py
```

```python
# line_profiler - line-by-line
# pip install line_profiler

@profile
def slow_function():
    ...

# Run with: kernprof -l -v script.py
```

```python
# memory_profiler
# pip install memory_profiler

@profile
def memory_heavy():
    ...

# Run with: python -m memory_profiler script.py
```

### TypeScript/JavaScript

```typescript
// Chrome DevTools / Node.js inspector
console.time('operation');
// ... code ...
console.timeEnd('operation');

// More detailed
const start = performance.now();
// ... code ...
const end = performance.now();
console.log(`Took ${end - start}ms`);
```

```bash
# Node.js profiling
node --prof app.js
node --prof-process isolate-*.log > profile.txt
```

## Performance Testing Patterns

### Benchmark Tests

```python
import pytest
import time

@pytest.fixture
def large_dataset():
    return list(range(100000))

def test_search_performance(large_dataset):
    """Performance: search completes in < 10ms for 100K items"""
    start = time.perf_counter()
    
    result = search(large_dataset, 50000)
    
    elapsed = time.perf_counter() - start
    assert elapsed < 0.010, f"Search took {elapsed*1000:.2f}ms, expected < 10ms"
```

### Scalability Tests

```python
@pytest.mark.parametrize("size", [1000, 10000, 100000])
def test_search_scales_logarithmically(size):
    """Performance: search time grows logarithmically"""
    data = list(range(size))
    
    times = []
    for _ in range(10):
        start = time.perf_counter()
        search(data, size // 2)
        times.append(time.perf_counter() - start)
    
    avg_time = sum(times) / len(times)
    # Log(100K) / Log(1K) ≈ 1.67, allow 3x for overhead
    expected_ratio = 3.0
    
    if size == 100000:
        assert avg_time < base_time * expected_ratio
```

### Memory Tests

```python
import tracemalloc

def test_memory_usage():
    """Performance: memory usage < 100MB for 10K items"""
    tracemalloc.start()
    
    processor = DataProcessor()
    processor.load(10000)
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    assert peak < 100 * 1024 * 1024, f"Peak memory: {peak / 1024 / 1024:.2f}MB"
```

## Common Performance Issues

### 1. O(n²) Algorithms

```python
# BAD: O(n²)
def find_duplicates(items):
    duplicates = []
    for i, item in enumerate(items):
        for j, other in enumerate(items):
            if i != j and item == other:
                duplicates.append(item)
    return duplicates

# GOOD: O(n)
def find_duplicates(items):
    seen = set()
    duplicates = set()
    for item in items:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return list(duplicates)
```

### 2. Repeated Database Queries (N+1)

```python
# BAD: N+1 queries
def get_users_with_posts():
    users = db.query("SELECT * FROM users")
    for user in users:
        user.posts = db.query(f"SELECT * FROM posts WHERE user_id = {user.id}")
    return users

# GOOD: 2 queries with join
def get_users_with_posts():
    return db.query("""
        SELECT u.*, p.* FROM users u
        LEFT JOIN posts p ON u.id = p.user_id
    """)
```

### 3. Unnecessary Object Creation

```python
# BAD: Creates new string each iteration
result = ""
for item in items:
    result += str(item)

# GOOD: Single join
result = "".join(str(item) for item in items)
```

### 4. Missing Caching

```python
# BAD: Recalculates every call
def get_expensive_result(key):
    return expensive_calculation(key)

# GOOD: Cache results
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_expensive_result(key):
    return expensive_calculation(key)
```

## Optimization Workflow

### 1. Measure First

```python
# Don't guess - measure!
import cProfile
cProfile.run('slow_function()', sort='cumulative')
```

### 2. Identify Bottleneck

Look for:
- Functions taking most time
- Functions called most often
- Unexpected time in simple operations

### 3. Update Spec (if needed)

If optimization changes interface:

```markdown
## Guardrails (updated)

- `search()` must use binary search (O(log n))
- Results are cached for 5 minutes
```

### 4. Implement Optimization

Follow the spec's new requirements.

### 5. Verify Improvement

```bash
# Run benchmark before and after
python -m pytest tests/test_performance.py -v
```

## Adding Performance to Specs

### Guardrails Section

```markdown
## Guardrails

### Time Complexity
- `search()`: O(log n)
- `sort()`: O(n log n)
- `get()`: O(1)

### Response Time
- API endpoints: < 200ms (p95)
- Batch operations: < 5s for 1000 items

### Memory
- Working set: < 500MB
- Per-request allocation: < 10MB

### Throughput
- Minimum: 100 requests/second
```

### Testing Contracts

```markdown
## Testing Contracts

### Performance Tests
- Benchmark tests for all time-critical operations
- Memory profiling for data-heavy operations
- Load tests for API endpoints
- Scalability tests (1K, 10K, 100K items)
```

## Docker Performance Testing

```bash
# Run performance tests in Docker
docker run --rm -v "$(pwd)":/workspace g5-runtime \
  python -m pytest /workspace/tests/test_performance.py -v --tb=short

# With profiling
docker run --rm -v "$(pwd)":/workspace g5-runtime \
  python -m cProfile -s cumulative /workspace/src/benchmark.py
```

## Common Mistakes

1. **Premature optimization** - Measure first, then optimize
2. **Optimizing the wrong thing** - Profile to find real bottleneck
3. **No benchmarks** - Can't improve what you don't measure
4. **Breaking correctness** - Tests must still pass
5. **Missing spec update** - Document performance requirements

## Performance Checklist

- [ ] Identified bottleneck with profiling
- [ ] Performance requirements in spec guardrails
- [ ] Benchmark tests written
- [ ] Optimization doesn't break functionality
- [ ] Before/after measurements documented
- [ ] Memory usage acceptable

> 💡 **Related skills**: 
> - [g5-spec-writing](../g5-spec-writing/SKILL.md) for performance guardrails
> - [g5-testgen](../g5-testgen/SKILL.md) for benchmark tests
> - [g5-debugging](../g5-debugging/SKILL.md) for test failures
