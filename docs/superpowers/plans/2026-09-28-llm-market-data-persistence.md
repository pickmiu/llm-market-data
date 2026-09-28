# OpenRouter Market Data Collection & Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a robust, lightweight OpenRouter market data collection and persistence pipeline executed via GitHub Actions, scheduled by a Cloudflare Worker cron trigger, storing JSON snapshots in `data/`, with rate-limited historical backfill.

**Architecture:** A decoupled GitOps pipeline where a Cloudflare Worker triggers a GitHub Actions workflow (`workflow_dispatch`) at UTC 00:30 (Beijing 08:30) following OpenRouter's "most recent complete day" settlement. The runner executes a Python sync engine that fetches `/models` pricing, scrapes web ranking SSR data, scans `data/openrouter/rankings_daily/` for missing dates within a configurable lookback window, safely backfills up to `max_requests` per run with 2.5s pacing and exponential backoff, and commits updated JSON files back to Git.

**Tech Stack:** Python 3.11+, `requests`, `pytest`, JavaScript/Wrangler (Cloudflare Workers), GitHub Actions YAML.

**Spec:** `docs/superpowers/specs/2026-09-28-llm-market-data-design.md`

## Global Constraints

- **Python Version**: Python 3.11+
- **Core Dependencies**: Lightweight only (`requests`, `python-dotenv`). No heavy data science/visualization frameworks (like matplotlib or pandas) in phase 1.
- **Test Framework**: `pytest`
- **Rate Limit Pacing**: Minimum 2.5s pause between consecutive HTTP calls to OpenRouter API (max 24 req/min, strictly below 30 req/min limit).
- **Retry Policy**: 3 exponential retries for 429 and 5xx (intervals: 5s, 10s, 20s).
- **Storage Paths**:
  - `data/openrouter/models/YYYY-MM-DD.json`
  - `data/openrouter/rankings_daily/YYYY-MM-DD.json`
  - `data/openrouter/web_rankings/YYYY-MM-DD.json`
- **Scheduler Cron**: `30 0 * * *` (UTC 00:30, Beijing 08:30).
- **Git Push Rule**: Agent must NEVER automatically push to remote Git repository without explicit confirmation from the human partner.

## Review Focus

1. **429 Rate Limit Exhaustion**: When OpenRouter returns HTTP 429 across all retries, the sync process must gracefully save all prior successful downloads, log an informative warning, and exit cleanly without corrupting existing JSON files.
2. **Corrupted or 0-Byte JSON Files**: If a previous run left a 0-byte or malformed `.json` file in `data/`, the scanner must treat it as missing rather than skipping it.
3. **Cloudflare Bot Challenge on Web Rankings**: If `https://openrouter.ai/rankings` crawler receives an anti-bot challenge (e.g. 403 or non-JSON HTML), it must log a non-fatal warning and allow the primary API `/models` and `/rankings-daily` workflows to succeed.
4. **Boundary Date Transitions**: On leap years or month boundaries (e.g. 2026-02-28 to 2026-03-01), the date sequence generator must generate valid `YYYY-MM-DD` strings in UTC without off-by-one errors.
5. **No-op Git Commits**: When all dates within the lookback window are already cached and no data changed, the GitHub Actions step must detect clean working tree and exit without error or creating empty Git commits.

---

### Task 1: Scaffolding, Core Dependencies & Directory Structure

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `sources/__init__.py`
- Create: `sources/openrouter/__init__.py`
- Create: `data/openrouter/models/.gitkeep`
- Create: `data/openrouter/rankings_daily/.gitkeep`
- Create: `data/openrouter/web_rankings/.gitkeep`
- Test: `tests/test_scaffold.py`

**Interfaces:**
- Consumes: None
- Produces: Project root structure, dependency specification, and data folder layout.

- [ ] **Step 1: Write failing test for scaffolding**

```python
# tests/test_scaffold.py
from pathlib import Path

def test_project_structure():
    root = Path(__file__).resolve().parent.parent
    assert (root / "requirements.txt").exists()
    assert (root / ".env.example").exists()
    assert (root / "sources" / "__init__.py").exists()
    assert (root / "sources" / "openrouter" / "__init__.py").exists()
    assert (root / "data" / "openrouter" / "models").is_dir()
    assert (root / "data" / "openrouter" / "rankings_daily").is_dir()
    assert (root / "data" / "openrouter" / "web_rankings").is_dir()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scaffold.py -v`
Expected: FAIL with `AssertionError: assert False` (missing files/dirs)

- [ ] **Step 3: Write minimal implementation**

1. Create `requirements.txt`:
```text
requests>=2.31.0
python-dotenv>=1.0.0
pytest>=8.0.0
```

2. Create `.env.example`:
```bash
OPENROUTER_API_KEY=your_openrouter_api_key_here
LOOKBACK_DAYS=90
MAX_REQUESTS_PER_RUN=40
```

3. Create `.gitignore`:
```gitignore
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.env
.venv/
env/
venv/
node_modules/
.wrangler/
```

4. Create directory markers and packages:
```bash
mkdir -p sources/openrouter
mkdir -p data/openrouter/models
mkdir -p data/openrouter/rankings_daily
mkdir -p data/openrouter/web_rankings
touch sources/__init__.py
touch sources/openrouter/__init__.py
touch data/openrouter/models/.gitkeep
touch data/openrouter/rankings_daily/.gitkeep
touch data/openrouter/web_rankings/.gitkeep
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scaffold.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .env.example .gitignore sources/ data/ tests/test_scaffold.py
git commit -m "chore: scaffold project structure and dependencies"
```

---

### Task 2: OpenRouter API Client with Rate Limiting & Backoff

**Files:**
- Create: `sources/openrouter/client.py`
- Test: `tests/test_client.py`

**Interfaces:**
- Consumes: `OPENROUTER_API_KEY` string, target endpoints (`/api/v1/models`, `/api/v1/datasets/rankings-daily`).
- Produces: `OpenRouterClient` class with methods:
  - `get_models() -> dict`
  - `get_rankings_daily(date: str) -> dict`
  - Configurable `rate_delay: float = 2.5` and `max_retries: int = 3`.

- [ ] **Step 1: Write failing test for OpenRouter client**

```python
# tests/test_client.py
import pytest
from unittest.mock import patch, MagicMock
from sources.openrouter.client import OpenRouterClient, OpenRouterAPIError

def test_client_init():
    client = OpenRouterClient(api_key="test-key", rate_delay=0.0)
    assert client.api_key == "test-key"
    assert client.rate_delay == 0.0

@patch("sources.openrouter.client.requests.get")
def test_get_models_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": [{"id": "openai/gpt-4o", "name": "GPT-4o"}]}
    mock_get.return_value = mock_resp

    client = OpenRouterClient(api_key=None, rate_delay=0.0)
    data = client.get_models()
    assert "data" in data
    assert data["data"][0]["id"] == "openai/gpt-4o"
    mock_get.assert_called_once_with(
        "https://openrouter.ai/api/v1/models",
        headers={"User-Agent": "LLM-Market-Data-Collector/1.0"},
        timeout=30
    )

@patch("sources.openrouter.client.requests.get")
def test_get_rankings_daily_requires_key(mock_get):
    client = OpenRouterClient(api_key=None, rate_delay=0.0)
    with pytest.raises(ValueError, match="API key is required"):
        client.get_rankings_daily("2026-09-27")

@patch("sources.openrouter.client.requests.get")
def test_get_rankings_daily_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [{"date": "2026-09-27", "model_permaslug": "openai/gpt-4o", "total_tokens": 1000}],
        "asOf": "2026-09-28T00:15:00Z"
    }
    mock_get.return_value = mock_resp

    client = OpenRouterClient(api_key="sk-test-key", rate_delay=0.0)
    res = client.get_rankings_daily("2026-09-27")
    assert res["data"][0]["model_permaslug"] == "openai/gpt-4o"
    mock_get.assert_called_once_with(
        "https://openrouter.ai/api/v1/datasets/rankings-daily",
        headers={
            "User-Agent": "LLM-Market-Data-Collector/1.0",
            "Authorization": "Bearer sk-test-key"
        },
        params={"date": "2026-09-27"},
        timeout=30
    )

@patch("sources.openrouter.client.time.sleep")
@patch("sources.openrouter.client.requests.get")
def test_retry_on_429(mock_get, mock_sleep):
    mock_429 = MagicMock(status_code=429)
    mock_200 = MagicMock(status_code=200)
    mock_200.json.return_value = {"data": []}
    mock_get.side_effect = [mock_429, mock_200]

    client = OpenRouterClient(api_key="sk-test", rate_delay=0.0, max_retries=2)
    res = client.get_rankings_daily("2026-09-27")
    assert res == {"data": []}
    assert mock_get.call_count == 2
    mock_sleep.assert_called()

@patch("sources.openrouter.client.time.sleep")
@patch("sources.openrouter.client.requests.get")
def test_exhausted_retries_raises_api_error(mock_get, mock_sleep):
    mock_429 = MagicMock(status_code=429)
    mock_get.return_value = mock_429

    client = OpenRouterClient(api_key="sk-test", rate_delay=0.0, max_retries=2)
    with pytest.raises(OpenRouterAPIError, match="Max retries exceeded"):
        client.get_rankings_daily("2026-09-27")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_client.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sources.openrouter.client'`

- [ ] **Step 3: Write minimal implementation**

```python
# sources/openrouter/client.py
import time
import requests
from typing import Optional, Dict, Any

class OpenRouterAPIError(Exception):
    """Custom exception raised when an OpenRouter API call fails."""
    pass

class OpenRouterClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        rate_delay: float = 2.5,
        max_retries: int = 3,
        timeout: int = 30
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.rate_delay = rate_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.user_agent = "LLM-Market-Data-Collector/1.0"
        self._last_request_time = 0.0

    def _apply_rate_pacing(self) -> None:
        """Enforces rate pacing delay between successive requests."""
        if self.rate_delay <= 0:
            return
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_delay:
            time.sleep(self.rate_delay - elapsed)
        self._last_request_time = time.time()

    def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        auth_required: bool = False
    ) -> Dict[str, Any]:
        if auth_required and not self.api_key:
            raise ValueError("OpenRouter API key is required for this endpoint")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {"User-Agent": self.user_agent}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        backoff_delays = [5.0, 10.0, 20.0]

        for attempt in range(self.max_retries + 1):
            self._apply_rate_pacing()
            try:
                resp = requests.get(url, headers=headers, params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code in (429, 500, 502, 503, 504):
                    if attempt < self.max_retries:
                        delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                        time.sleep(delay)
                        continue
                    raise OpenRouterAPIError(f"Max retries exceeded for {url}: HTTP {resp.status_code}")
                else:
                    raise OpenRouterAPIError(f"HTTP {resp.status_code} error from {url}: {resp.text}")
            except (requests.RequestException) as exc:
                if attempt < self.max_retries:
                    delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                    time.sleep(delay)
                    continue
                raise OpenRouterAPIError(f"Request failed for {url}: {exc}") from exc

        raise OpenRouterAPIError(f"Failed to fetch {url} after {self.max_retries} retries")

    def get_models(self) -> Dict[str, Any]:
        """Fetch models list and pricing (public, no auth required)."""
        return self._request("models", auth_required=False)

    def get_rankings_daily(self, date: str) -> Dict[str, Any]:
        """Fetch daily rankings for a specific date (requires API key)."""
        return self._request("datasets/rankings-daily", params={"date": date}, auth_required=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_client.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add sources/openrouter/client.py tests/test_client.py
git commit -m "feat(sources): implement OpenRouter API client with rate pacing and backoff"
```

---

### Task 3: OpenRouter Web Rankings Crawler

**Files:**
- Create: `sources/openrouter/crawler.py`
- Test: `tests/test_crawler.py`

**Interfaces:**
- Consumes: Public URL `https://openrouter.ai/rankings`.
- Produces: `OpenRouterWebCrawler` class with method:
  - `crawl_rankings() -> dict`: returns dictionary containing parsed tables: `today`, `trailing_30_days`, `new_and_trending`.
  - Non-fatal error handling: returns `{"error": str, "tables": {}}` when blocked by anti-bot.

- [ ] **Step 1: Write failing test for web crawler**

```python
# tests/test_crawler.py
from unittest.mock import patch, MagicMock
from sources.openrouter.crawler import OpenRouterWebCrawler

SAMPLE_SSR_HTML = """
<html>
<body>
<div hidden id="S:3">
<div class="sr-only">
<h3>Top models today, as text</h3>
<p>Text summary of the Today tab of the leaderboard above.</p>
<table>
<thead><tr><th>Rank</th><th>Model</th><th>Author</th><th>Tokens</th><th>Change</th></tr></thead>
<tbody>
<tr><td>1</td><td>z-ai/glm-5</td><td>z-ai</td><td>57.5T</td><td>+10%</td></tr>
<tr><td>2</td><td>openai/gpt-4o</td><td>openai</td><td>40T</td><td>-5%</td></tr>
</tbody>
</table>
</div>
</div>
<div class="sr-only">
<h3>Top models this month, as text</h3>
<p>Text summary of the This Month tab of the leaderboard above. Models are ranked by tokens processed on OpenRouter over the trailing thirty days.</p>
<table>
<tbody>
<tr><td>1</td><td>anthropic/claude-3.5-sonnet</td><td>anthropic</td><td>100T</td><td>+20%</td></tr>
</tbody>
</table>
</div>
</body>
</html>
"""

def test_crawler_init():
    crawler = OpenRouterWebCrawler(url="https://openrouter.ai/rankings")
    assert crawler.url == "https://openrouter.ai/rankings"

@patch("sources.openrouter.crawler.requests.get")
def test_crawl_rankings_success(mock_get):
    mock_resp = MagicMock(status_code=200, text=SAMPLE_SSR_HTML)
    mock_get.return_value = mock_resp

    crawler = OpenRouterWebCrawler()
    result = crawler.crawl_rankings()

    assert result["status"] == "ok"
    assert "today" in result["tables"]
    assert len(result["tables"]["today"]) == 2
    assert result["tables"]["today"][0]["model"] == "z-ai/glm-5"
    assert result["tables"]["today"][0]["tokens"] == "57.5T"
    assert "trailing_30_days" in result["tables"]
    assert result["tables"]["trailing_30_days"][0]["author"] == "anthropic"

@patch("sources.openrouter.crawler.requests.get")
def test_crawl_rankings_cloudflare_blocked_graceful(mock_get):
    mock_resp = MagicMock(status_code=403, text="<html>Cloudflare Challenge</html>")
    mock_get.return_value = mock_resp

    crawler = OpenRouterWebCrawler()
    result = crawler.crawl_rankings()

    assert result["status"] == "blocked"
    assert result["tables"] == {}
    assert "error" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_crawler.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sources.openrouter.crawler'`

- [ ] **Step 3: Write minimal implementation**

```python
# sources/openrouter/crawler.py
import re
import requests
from typing import Dict, Any, List

class OpenRouterWebCrawler:
    def __init__(self, url: str = "https://openrouter.ai/rankings", timeout: int = 15):
        self.url = url
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }

    def _parse_table_rows(self, table_html: str) -> List[Dict[str, str]]:
        rows = []
        tr_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
        for tr in tr_matches:
            tds = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.DOTALL | re.IGNORECASE)
            if len(tds) >= 4:
                clean_tds = [re.sub(r'<[^>]+>', '', td).strip() for td in tds]
                row_data = {
                    "rank": clean_tds[0] if len(clean_tds) > 0 else "",
                    "model": clean_tds[1] if len(clean_tds) > 1 else "",
                    "author": clean_tds[2] if len(clean_tds) > 2 else "",
                    "tokens": clean_tds[3] if len(clean_tds) > 3 else "",
                    "change": clean_tds[4] if len(clean_tds) > 4 else ""
                }
                rows.append(row_data)
        return rows

    def crawl_rankings(self) -> Dict[str, Any]:
        """Scrapes web leaderboard tables from SSR embedded HTML."""
        try:
            resp = requests.get(self.url, headers=self.headers, timeout=self.timeout)
            if resp.status_code != 200:
                return {
                    "status": "blocked" if resp.status_code in (403, 503) else "error",
                    "error": f"HTTP {resp.status_code}",
                    "tables": {}
                }

            html = resp.text
            tables = {}

            # Pattern for Today tab
            today_match = re.search(r'Top models today, as text.*?<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
            if today_match:
                tables["today"] = self._parse_table_rows(today_match.group(1))

            # Pattern for This Month tab (trailing thirty days)
            month_match = re.search(r'Top models this month, as text.*?<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
            if month_match:
                tables["trailing_30_days"] = self._parse_table_rows(month_match.group(1))

            # Pattern for New & Trending tab
            trending_match = re.search(r'New &amp; Trending tab.*?<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
            if trending_match:
                tables["new_and_trending"] = self._parse_table_rows(trending_match.group(1))

            return {
                "status": "ok",
                "tables": tables
            }
        except Exception as exc:
            return {
                "status": "error",
                "error": str(exc),
                "tables": {}
            }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_crawler.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add sources/openrouter/crawler.py tests/test_crawler.py
git commit -m "feat(sources): implement OpenRouter SSR web rankings crawler"
```

---

### Task 4: Sync Engine & Rate-Limited Historical Backfill

**Files:**
- Create: `sources/openrouter/sync.py`
- Test: `tests/test_sync.py`

**Interfaces:**
- Consumes: `OpenRouterClient`, `OpenRouterWebCrawler`, local `data_dir: Path`.
- Produces: `find_missing_dates()`, `sync_models()`, `sync_web_rankings()`, `sync_rankings_daily()`, and main `run_sync()` function.

- [ ] **Step 1: Write failing test for sync engine**

```python
# tests/test_sync.py
import json
import datetime
from pathlib import Path
from unittest.mock import MagicMock
from sources.openrouter.sync import (
    find_missing_dates,
    sync_models,
    sync_web_rankings,
    sync_rankings_daily,
    run_sync
)

def test_find_missing_dates(tmp_path):
    rankings_dir = tmp_path / "data" / "openrouter" / "rankings_daily"
    rankings_dir.mkdir(parents=True)

    # Simulate existing valid file
    valid_file = rankings_dir / "2026-09-25.json"
    valid_file.write_text(json.dumps({"data": []}))

    # Simulate empty corrupted file (should be treated as missing)
    empty_file = rankings_dir / "2026-09-26.json"
    empty_file.write_text("")

    start = datetime.date(2026, 9, 24)
    end = datetime.date(2026, 9, 27)

    missing = find_missing_dates(rankings_dir, start, end)
    # Expected reverse order: 2026-09-27, 2026-09-26, 2026-09-24 (25 exists and valid)
    assert missing == ["2026-09-27", "2026-09-26", "2026-09-24"]

def test_sync_models_saves_file(tmp_path):
    client = MagicMock()
    client.get_models.return_value = {"data": [{"id": "test-model"}]}

    out_file = sync_models(client, tmp_path, target_date="2026-09-28")
    assert out_file.exists()
    content = json.loads(out_file.read_text())
    assert content["date"] == "2026-09-28"
    assert content["data"][0]["id"] == "test-model"

def test_sync_models_idempotent_skip(tmp_path):
    client = MagicMock()
    models_dir = tmp_path / "models"
    models_dir.mkdir(parents=True)
    existing = models_dir / "2026-09-28.json"
    existing.write_text(json.dumps({"date": "2026-09-28", "data": []}))

    sync_models(client, tmp_path, target_date="2026-09-28", force=False)
    client.get_models.assert_not_called()

def test_sync_rankings_daily_respects_max_requests(tmp_path):
    client = MagicMock()
    client.get_rankings_daily.return_value = {"data": [], "asOf": "2026-09-28T00:00:00Z"}

    missing_dates = ["2026-09-27", "2026-09-26", "2026-09-25", "2026-09-24"]
    stats = sync_rankings_daily(client, tmp_path, missing_dates, max_requests=2)

    assert stats["fetched"] == 2
    assert stats["remaining"] == 2
    assert client.get_rankings_daily.call_count == 2
    assert (tmp_path / "rankings_daily" / "2026-09-27.json").exists()
    assert (tmp_path / "rankings_daily" / "2026-09-26.json").exists()
    assert not (tmp_path / "rankings_daily" / "2026-09-25.json").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_sync.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sources.openrouter.sync'`

- [ ] **Step 3: Write minimal implementation**

```python
# sources/openrouter/sync.py
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from sources.openrouter.client import OpenRouterClient, OpenRouterAPIError
from sources.openrouter.crawler import OpenRouterWebCrawler

def is_valid_json_file(file_path: Path) -> bool:
    """Checks whether file exists, has content > 0 bytes, and contains valid JSON."""
    if not file_path.exists() or file_path.stat().st_size == 0:
        return False
    try:
        with file_path.open("r", encoding="utf-8") as f:
            json.load(f)
        return True
    except Exception:
        return False

def find_missing_dates(
    rankings_dir: Path,
    start_date: datetime.date,
    end_date: datetime.date
) -> List[str]:
    """Scans date range and returns missing/invalid dates in reverse order (newest first)."""
    rankings_dir.mkdir(parents=True, exist_ok=True)
    missing = []
    curr = end_date
    while curr >= start_date:
        date_str = curr.strftime("%Y-%m-%d")
        file_path = rankings_dir / f"{date_str}.json"
        if not is_valid_json_file(file_path):
            missing.append(date_str)
        curr -= datetime.timedelta(days=1)
    return missing

def sync_models(
    client: OpenRouterClient,
    data_dir: Path,
    target_date: str,
    force: bool = False
) -> Path:
    """Fetches and persists OpenRouter model metadata and pricing snapshot."""
    models_dir = data_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    out_file = models_dir / f"{target_date}.json"

    if not force and is_valid_json_file(out_file):
        return out_file

    payload = client.get_models()
    snapshot = {
        "date": target_date,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "data": payload.get("data", [])
    }
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    return out_file

def sync_web_rankings(
    crawler: OpenRouterWebCrawler,
    data_dir: Path,
    target_date: str,
    force: bool = False
) -> Path:
    """Fetches and persists OpenRouter SSR web rankings snapshot."""
    web_dir = data_dir / "web_rankings"
    web_dir.mkdir(parents=True, exist_ok=True)
    out_file = web_dir / f"{target_date}.json"

    if not force and is_valid_json_file(out_file):
        return out_file

    crawl_res = crawler.crawl_rankings()
    snapshot = {
        "date": target_date,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": crawl_res.get("status"),
        "error": crawl_res.get("error"),
        "tables": crawl_res.get("tables", {})
    }
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    return out_file

def sync_rankings_daily(
    client: OpenRouterClient,
    data_dir: Path,
    missing_dates: List[str],
    max_requests: int = 40,
    force: bool = False
) -> Dict[str, Any]:
    """Iterates through missing dates and backfills rankings_daily within max_requests."""
    rankings_dir = data_dir / "rankings_daily"
    rankings_dir.mkdir(parents=True, exist_ok=True)

    fetched = 0
    failed = []

    for date_str in missing_dates:
        if fetched >= max_requests:
            break
        out_file = rankings_dir / f"{date_str}.json"
        if not force and is_valid_json_file(out_file):
            continue

        try:
            res = client.get_rankings_daily(date_str)
            snapshot = {
                "date": date_str,
                "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "as_of": res.get("asOf"),
                "data": res.get("data", [])
            }
            with out_file.open("w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)
            fetched += 1
        except OpenRouterAPIError as exc:
            failed.append({"date": date_str, "error": str(exc)})
            # Break early on persistent failure (e.g. rate limit exhausted) to prevent wasting quota
            break

    remaining = len(missing_dates) - fetched
    return {
        "fetched": fetched,
        "remaining": remaining,
        "failed": failed
    }

def run_sync(
    data_dir: Path,
    api_key: Optional[str] = None,
    lookback_days: int = 90,
    max_requests: int = 40,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    force: bool = False,
    only: Optional[str] = None
) -> Dict[str, Any]:
    """Orchestrates sync pipeline across models, web_rankings, and rankings_daily."""
    today_utc = datetime.datetime.now(datetime.timezone.utc).date()
    yesterday_utc = today_utc - datetime.timedelta(days=1)
    today_str = today_utc.strftime("%Y-%m-%d")

    client = OpenRouterClient(api_key=api_key)
    crawler = OpenRouterWebCrawler()
    results = {}

    # 1. Sync models
    if only in (None, "models"):
        models_file = sync_models(client, data_dir, today_str, force=force)
        results["models"] = str(models_file)

    # 2. Sync web rankings
    if only in (None, "web"):
        web_file = sync_web_rankings(crawler, data_dir, today_str, force=force)
        results["web_rankings"] = str(web_file)

    # 3. Sync rankings daily
    if only in (None, "rankings"):
        if end_date:
            e_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            e_dt = yesterday_utc

        if start_date:
            s_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            s_dt = e_dt - datetime.timedelta(days=lookback_days - 1)

        rankings_dir = data_dir / "rankings_daily"
        missing = find_missing_dates(rankings_dir, s_dt, e_dt)
        rankings_stats = sync_rankings_daily(
            client=client,
            data_dir=data_dir,
            missing_dates=missing,
            max_requests=max_requests,
            force=force
        )
        results["rankings_daily"] = rankings_stats

    return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_sync.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add sources/openrouter/sync.py tests/test_sync.py
git commit -m "feat(sources): implement sync engine with date scanning and rate-limited backfill"
```

---

### Task 5: Unified CLI Entry Point (`cli.py`)

**Files:**
- Create: `cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: Command line arguments (`sync`, `--lookback-days`, `--max-requests`, `--start-date`, `--end-date`, `--force`, `--only`), environment variables (`OPENROUTER_API_KEY`, `LOOKBACK_DAYS`, `MAX_REQUESTS_PER_RUN`).
- Produces: CLI application with formatted console logging and proper exit codes (0 for success, non-zero for fatal error).

- [ ] **Step 1: Write failing test for CLI**

```python
# tests/test_cli.py
from unittest.mock import patch
from cli import build_parser, main

def test_cli_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["sync"])
    assert args.command == "sync"
    assert args.lookback_days == 90
    assert args.max_requests == 40
    assert args.force is False
    assert args.only is None

def test_cli_parser_custom_args():
    parser = build_parser()
    args = parser.parse_args([
        "sync",
        "--lookback-days", "30",
        "--max-requests", "20",
        "--start-date", "2026-08-01",
        "--end-date", "2026-08-31",
        "--force",
        "--only", "rankings"
    ])
    assert args.lookback_days == 30
    assert args.max_requests == 20
    assert args.start_date == "2026-08-01"
    assert args.end_date == "2026-08-31"
    assert args.force is True
    assert args.only == "rankings"

@patch("cli.run_sync")
def test_cli_main_executes_sync(mock_run_sync):
    mock_run_sync.return_value = {
        "models": "data/openrouter/models/2026-09-28.json",
        "rankings_daily": {"fetched": 2, "remaining": 0, "failed": []}
    }
    exit_code = main(["sync", "--lookback-days", "7"])
    assert exit_code == 0
    mock_run_sync.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cli'`

- [ ] **Step 3: Write minimal implementation**

```python
# cli.py
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from sources.openrouter.sync import run_sync

load_dotenv()

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LLM Market Data CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Synchronize OpenRouter datasets")
    sync_parser.add_argument(
        "--lookback-days",
        type=int,
        default=int(os.getenv("LOOKBACK_DAYS", "90")),
        help="Number of past days to scan for missing daily rankings (default: 90)"
    )
    sync_parser.add_argument(
        "--max-requests",
        type=int,
        default=int(os.getenv("MAX_REQUESTS_PER_RUN", "40")),
        help="Maximum API requests to spend on backfilling missing days in this run (default: 40)"
    )
    sync_parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Fixed start date for backfill (YYYY-MM-DD)"
    )
    sync_parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="Fixed end date for backfill (YYYY-MM-DD)"
    )
    sync_parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing snapshot files"
    )
    sync_parser.add_argument(
        "--only",
        choices=["models", "rankings", "web"],
        default=None,
        help="Sync only specified target (models, rankings, or web)"
    )

    return parser

def main(args: list = None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(args)

    if parsed.command == "sync":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key and parsed.only != "models":
            print("[Warning] OPENROUTER_API_KEY is not set. Rankings daily API calls will fail.")

        data_dir = Path(__file__).resolve().parent / "data" / "openrouter"

        print(f"[*] Starting OpenRouter sync (lookback: {parsed.lookback_days}d, max_requests: {parsed.max_requests})...")
        try:
            results = run_sync(
                data_dir=data_dir,
                api_key=api_key,
                lookback_days=parsed.lookback_days,
                max_requests=parsed.max_requests,
                start_date=parsed.start_date,
                end_date=parsed.end_date,
                force=parsed.force,
                only=parsed.only
            )
            print("[+] Sync completed successfully:")
            if "models" in results:
                print(f"  - Models snapshot: {results['models']}")
            if "web_rankings" in results:
                print(f"  - Web rankings snapshot: {results['web_rankings']}")
            if "rankings_daily" in results:
                stats = results["rankings_daily"]
                print(f"  - Daily rankings: fetched {stats['fetched']} days, remaining missing {stats['remaining']} days")
                if stats["failed"]:
                    print(f"  - Failed items: {stats['failed']}")
            return 0
        except Exception as exc:
            print(f"[!] Sync failed: {exc}", file=sys.stderr)
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add cli.py tests/test_cli.py
git commit -m "feat(cli): add unified CLI entry point for OpenRouter data sync"
```

---

### Task 6: Cloudflare Worker Scheduler & GitHub Actions CI/CD Pipeline

**Files:**
- Create: `deploy/cloudflare/wrangler.toml`
- Create: `deploy/cloudflare/worker.js`
- Create: `.github/workflows/collector.yml`
- Test: `tests/test_deploy.py`

**Interfaces:**
- Consumes: GitHub Actions `workflow_dispatch` trigger, `GITHUB_PAT` secret, `OPENROUTER_API_KEY` secret.
- Produces: Scheduled pipeline deploying at UTC 00:30, triggering runner, synchronizing data, and auto-committing diffs.

- [ ] **Step 1: Write failing test for Cloudflare Worker & GitHub Action config integrity**

```python
# tests/test_deploy.py
from pathlib import Path

def test_deploy_configs_exist():
    root = Path(__file__).resolve().parent.parent
    wrangler_file = root / "deploy" / "cloudflare" / "wrangler.toml"
    worker_file = root / "deploy" / "cloudflare" / "worker.js"
    workflow_file = root / ".github" / "workflows" / "collector.yml"

    assert wrangler_file.exists()
    assert worker_file.exists()
    assert workflow_file.exists()

    wrangler_text = wrangler_file.read_text()
    assert 'crons = ["30 0 * * *"]' in wrangler_text

    worker_text = worker_file.read_text()
    assert "workflow_dispatch" in worker_text or "dispatches" in worker_text
    assert "GITHUB_PAT" in worker_text

    workflow_text = workflow_file.read_text()
    assert "workflow_dispatch:" in workflow_text
    assert "python cli.py sync" in workflow_text
    assert "OPENROUTER_API_KEY" in workflow_text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_deploy.py -v`
Expected: FAIL with `AssertionError` (files not yet created)

- [ ] **Step 3: Write minimal implementation**

1. Create `deploy/cloudflare/wrangler.toml`:
```toml
name = "llm-market-data-scheduler"
main = "worker.js"
compatibility_date = "2026-09-28"

[triggers]
crons = ["30 0 * * *"]
```

2. Create `deploy/cloudflare/worker.js`:
```javascript
export default {
  async scheduled(event, env, ctx) {
    const owner = env.GITHUB_OWNER;
    const repo = env.GITHUB_REPO;
    const workflowFile = env.WORKFLOW_FILE || "collector.yml";
    const pat = env.GITHUB_PAT;
    const lookbackDays = env.LOOKBACK_DAYS || "90";
    const maxRequests = env.MAX_REQUESTS_PER_RUN || "40";

    if (!owner || !repo || !pat) {
      console.error("Missing required env vars: GITHUB_OWNER, GITHUB_REPO, GITHUB_PAT");
      return;
    }

    const url = `https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflowFile}/dispatches`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${pat}`,
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "CF-Worker-Market-Scheduler"
      },
      body: JSON.stringify({
        ref: "main",
        inputs: {
          lookback_days: lookbackDays,
          max_requests: maxRequests
        }
      })
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error(`Failed to dispatch GitHub workflow: HTTP ${response.status} - ${errText}`);
    } else {
      console.log(`Successfully triggered ${workflowFile} on ${owner}/${repo}`);
    }
  }
};
```

3. Create `.github/workflows/collector.yml`:
```yaml
name: OpenRouter Data Collector

on:
  workflow_dispatch:
    inputs:
      lookback_days:
        description: 'Number of days to look back for missing rankings'
        required: false
        default: '90'
      max_requests:
        description: 'Maximum API requests for backfilling in this run'
        required: false
        default: '40'
  schedule:
    # Secondary backup trigger: 01:30 UTC daily
    - cron: '30 1 * * *'

permissions:
  contents: write

jobs:
  collect:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run data synchronization
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
        run: |
          python cli.py sync \
            --lookback-days "${{ github.event.inputs.lookback_days || '90' }}" \
            --max-requests "${{ github.event.inputs.max_requests || '40' }}"

      - name: Commit and push changes
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add data/
          if git diff --staged --quiet; then
            echo "No data changes detected. Skipping commit."
          else
            git commit -m "chore(data): auto-sync openrouter market data [skip ci]"
            git push origin main
          fi
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_deploy.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add deploy/ .github/ tests/test_deploy.py
git commit -m "feat(deploy): add Cloudflare Worker scheduler and GitHub Actions collector workflow"
```

---

## Plan Self-Review Checklist

- [x] **Spec coverage**:
  - OpenRouter API models & daily rankings (/models & /rankings-daily) -> Covered in Task 2 & Task 4.
  - Web rankings crawler for SSR data -> Covered in Task 3.
  - Rate limiting & 2.5s pacing & exponential backoff -> Covered in Task 2 & Task 4.
  - Configurable lookback days & auto backfill -> Covered in Task 4 & Task 5.
  - Cloudflare Worker UTC 00:30 cron dispatch -> Covered in Task 6.
  - GitHub Actions auto-commit with `[skip ci]` -> Covered in Task 6.
  - Report module deferred per user instructions -> Documented as deferred.
- [x] **Placeholder scan**: All tasks contain explicit code, tests, and configuration without any "TODO", "TBD", or placeholders.
- [x] **Type consistency**: Standard Python types and signatures (`find_missing_dates(rankings_dir, start_date, end_date)`, `sync_models(client, data_dir, target_date, force)`, etc.) match across all tasks.
- [x] **Review Focus**: Handled 429 exhaustion, corrupted JSON check, Cloudflare bot challenge graceful degradation, and no-op Git commits.
