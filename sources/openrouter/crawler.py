import logging
import requests
from typing import Dict, Any

class OpenRouterWebCrawler:
    """Client for OpenRouter frontend public leaderboards (apps, task-spend, session-cost, benchmarks, performance)."""
    def __init__(self, base_url: str = "https://openrouter.ai/api/frontend/v1/rankings", timeout: int = 20):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        }

    def _fetch_json(self, endpoint: str) -> Dict[str, Any]:
        """Helper to fetch from frontend JSON endpoint with non-fatal error handling."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                return {"status": "ok", "data": data, "error": None}
            else:
                logging.warning("Failed to fetch %s: HTTP %s", url, resp.status_code)
                return {
                    "status": "error",
                    "data": {},
                    "error": f"HTTP {resp.status_code}: {resp.text[:200]}"
                }
        except Exception as e:
            logging.warning("Exception fetching %s: %s", url, e)
            return {"status": "error", "data": {}, "error": str(e)}

    def fetch_apps(self) -> Dict[str, Any]:
        """Fetches apps rankings (coding agents & applications leaderboard)."""
        return self._fetch_json("apps")

    def fetch_task_spend(self) -> Dict[str, Any]:
        """Fetches task spend data (macroCategories, tasks, model shares)."""
        return self._fetch_json("task-spend")

    def fetch_session_cost(self) -> Dict[str, Any]:
        """Fetches cost per session data across harnesses and buckets."""
        return self._fetch_json("session-cost")

    def fetch_benchmarks(self) -> Dict[str, Any]:
        """Fetches benchmarks data (Artificial Analysis index, coding, agentic, weighted input prices)."""
        return self._fetch_json("benchmarks")

    def fetch_performance(self) -> Dict[str, Any]:
        """Fetches performance data (throughput tok/s, latency, best providers and prices)."""
        return self._fetch_json("performance")

OpenRouterFrontendClient = OpenRouterWebCrawler
