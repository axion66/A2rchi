---
type: spec
module: data_manager.collectors.scrapers
version: "1.0"
status: extracted
test_file: tests/unit/test_scrapers.py
source_files:
  - src/data_manager/collectors/scrapers/scraper_manager.py
  - src/data_manager/collectors/scrapers/scraper.py
  - src/data_manager/collectors/scrapers/scraped_resource.py
---

# Scrapers Spec

## Overview

Web scraping infrastructure for collecting documents from URLs. Supports link lists, git repositories, and SSO-authenticated sites.

## Dependencies

- `src/data_manager/collectors/persistence.PersistenceService`
- `src/data_manager/collectors/scrapers/scraped_resource.ScrapedResource`
- `src/data_manager/collectors/scrapers/scraper.LinkScraper`

## Public API

### Classes

#### `ScraperManager`
```python
class ScraperManager:
    """Coordinates scraper integrations and centralizes persistence logic."""
    
    config: Dict
    data_path: Path
    input_lists: List[str]
    base_depth: int
    max_pages: Optional[int]
    
    # Feature flags
    links_enabled: bool
    git_enabled: bool
    selenium_enabled: bool
    scrape_with_selenium: bool
    
    # Scrapers
    web_scraper: LinkScraper
    _git_scraper: Optional[GitScraper]
```

**Constructor:**
```python
def __init__(self, dm_config: Optional[Dict[str, Any]] = None) -> None
```

**Contracts:**
- ENSURES: Loads global and utils config
- ENSURES: Initializes `LinkScraper` with config
- ENSURES: Creates `data_path` directory

**Methods:**

##### `collect`
```python
def collect(self, persistence: PersistenceService) -> None
```
Run configured scrapers and persist output.

**Contracts:**
- ENSURES: Resets websites directory if `reset_data=True`
- ENSURES: Skips all scraping if `links_enabled=False`
- ENSURES: Processes URLs from input lists
- ENSURES: Routes `git-` prefixed URLs to git scraper
- ENSURES: Routes `sso-` prefixed URLs through authenticator
- ENSURES: Persists all scraped resources

##### `collect_urls_from_lists`
```python
def collect_urls_from_lists(self) -> Iterator[Tuple[str, int]]
```
Yield (url, depth) pairs from input list files.

---

#### `LinkScraper`
```python
class LinkScraper:
    """Scrapes web pages and follows links to configured depth."""
    
    verify_urls: bool
    enable_warnings: bool
```

**Methods:**

##### `scrape`
```python
def scrape(
    self,
    url: str,
    depth: int,
    max_pages: Optional[int] = None,
    selenium_client: Optional[Any] = None
) -> List[ScrapedResource]
```
Scrape URL and follow links to depth.

**Contracts:**
- ENSURES: Returns list of `ScrapedResource` objects
- ENSURES: Respects `max_pages` limit
- ENSURES: Uses Selenium if client provided

---

#### `ScrapedResource`
```python
class ScrapedResource(BaseResource):
    """Resource representing a scraped web page."""
    
    url: str
    content: str
    title: Optional[str]
    source_type: str = "web"
```

**Methods:**

##### `get_hash`
```python
def get_hash(self) -> str
```
Return hash based on URL.

##### `get_filename`
```python
def get_filename(self) -> str
```
Return sanitized filename from URL.

##### `get_content`
```python
def get_content(self) -> str
```
Return HTML content.

##### `get_metadata`
```python
def get_metadata(self) -> ResourceMetadata
```
Return metadata with URL, title, timestamp.

## Configuration

```yaml
data_manager:
  sources:
    links:
      enabled: true
      input_lists: ["urls.list", "docs.list"]
      base_source_depth: 5
      max_pages: 100
      html_scraper:
        verify_urls: true
        reset_data: false
      selenium_scraper:
        enabled: false
        use_for_scraping: false
    git:
      enabled: false
```

## URL Prefixes

| Prefix | Behavior |
|--------|----------|
| (none) | Standard web scraping |
| `git-` | Routed to GitScraper |
| `sso-` | Authenticated via Selenium |

## Invariants

1. Each URL scraped at most once per run
2. Depth controls link following, not initial URL
3. Selenium client shared across batch
