---
spec_id: utils/benchmark-report
type: module
source_files:
  - src/utils/generate_benchmark_report.py
test_file: null
status: extracted
---

# Benchmark Report Generator

> ⚠️ **AUTO-GENERATED FROM CODE**: Review for accuracy.

## Overview

CLI tool to generate HTML reports from A2rchi benchmark results. Displays questions, answers, expected answers, retrieved contexts, and RAGAS scores.

## Structured Design Doc

### Functions

#### `load_benchmark_results(filepath: str) -> tuple[list, dict]`

Load benchmark results JSON file.

**Contracts:**
- PRE: `filepath` exists and is valid JSON
- POST: Returns `(data['benchmarking_results'], data['metadata'])`
- ERROR: `FileNotFoundError` if file missing

#### `parse_benchmark_results(results: list, metadata: dict) -> tuple`

Parse loaded results into components.

**Contracts:**
- PRE: `results` is non-empty list
- POST: Returns `(config_data, config_name, timestamp, questions, total_results)`

#### `format_html_output(...) -> str`

Generate HTML report from parsed data.

**Contracts:**
- POST: Returns valid HTML5 document
- POST: Includes retrieval accuracy section if SOURCES mode enabled
- POST: Includes aggregate RAGAS metrics if RAGAS mode enabled

#### `main() -> None`

CLI entry point.

**Contracts:**
- PRE: First positional arg is results JSON file path
- POST: Generates HTML file (default: `{input_stem}.html`)
- POST: Accepts `--html_output` for custom output path

### CLI Usage

```bash
python generate_benchmark_report.py results.json
python generate_benchmark_report.py results.json --html_output report.html
```

## Guardrails

- HTML-escapes user content to prevent XSS
- Truncates long contexts (500 chars) with expandable full text
- Color-codes scores: red (<0.5), yellow (0.5-0.7), green (>0.7)

## Testing Contracts

- Load valid JSON returns benchmarking_results and metadata
- HTML output is valid HTML5
