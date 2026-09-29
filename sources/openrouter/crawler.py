import re
import json
import logging
import requests
from typing import Dict, Any

class OpenRouterWebCrawler:
    """Client for OpenRouter frontend public leaderboards (apps, task-spend, session-cost, benchmarks, performance, transcription, coding_apps)."""
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

    def fetch_transcription(self) -> Dict[str, Any]:
        """Fetches Transcription (Speech-to-Text) leaderboard from openrouter.ai/rankings/transcription."""
        url = "https://openrouter.ai/rankings/transcription"
        try:
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            if resp.status_code != 200:
                logging.warning("Failed to fetch %s: HTTP %s", url, resp.status_code)
                return {
                    "status": "error",
                    "data": {},
                    "error": f"HTTP {resp.status_code}: {resp.text[:200]}"
                }

            raw = resp.text
            # 1. Primary: Extract embedded JSON array of model stats from Next.js SSR flight data
            idx = raw.find("model_permaslug")
            if idx != -1:
                start_arr = raw.rfind("[", 0, idx)
                if start_arr != -1:
                    bracket_count = 0
                    end_arr = -1
                    for i in range(start_arr, len(raw)):
                        if raw[i] == "[":
                            bracket_count += 1
                        elif raw[i] == "]":
                            bracket_count -= 1
                            if bracket_count == 0:
                                end_arr = i + 1
                                break
                    if end_arr != -1:
                        arr_str = raw[start_arr:end_arr]
                        unescaped = arr_str.replace(r'\"', '"').replace(r'\\', '\\')
                        try:
                            models_data = json.loads(unescaped)
                            if isinstance(models_data, list):
                                models_data = sorted(
                                    models_data,
                                    key=lambda x: x.get("count", 0) if isinstance(x, dict) else 0,
                                    reverse=True
                                )
                                return {"status": "ok", "data": {"models": models_data}, "error": None}
                        except Exception as parse_err:
                            logging.warning("Failed to parse Next.js flight data for transcription: %s", parse_err)

            # 2. Fallback: Parse HTML table rows
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', raw, re.DOTALL)
            table_models = []
            for r in rows:
                cells = re.findall(r'<(?:td|th)[^>]*>(.*?)</(?:td|th)>', r, re.DOTALL)
                cleaned = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
                if len(cleaned) >= 5 and cleaned[0].isdigit():
                    table_models.append({
                        "rank": int(cleaned[0]),
                        "name": cleaned[1],
                        "author": cleaned[2],
                        "requests_str": cleaned[3],
                        "change_str": cleaned[4]
                    })
            if table_models:
                return {"status": "ok", "data": {"models": table_models}, "error": None}

            return {"status": "error", "data": {}, "error": "Could not extract transcription models from page"}
        except Exception as e:
            logging.warning("Exception fetching transcription rankings: %s", e)
            return {"status": "error", "data": {}, "error": str(e)}

    def fetch_coding_apps(self, include_subcategories: bool = True) -> Dict[str, Any]:
        """Fetches Coding Agents 52-week historical token time series and latest leaderboard."""
        chart_url = "https://openrouter.ai/api/frontend/v1/apps/marketplace/category-chart?group=coding"
        category_url = "https://openrouter.ai/api/frontend/v1/apps/marketplace/category?group=coding"
        try:
            resp_chart = requests.get(chart_url, headers=self.headers, timeout=self.timeout)
            if resp_chart.status_code != 200:
                logging.warning("Failed to fetch coding apps chart: HTTP %s", resp_chart.status_code)
                return {
                    "status": "error",
                    "data": {},
                    "error": f"HTTP {resp_chart.status_code}: {resp_chart.text[:200]}"
                }
            chart_data = resp_chart.json().get("data", {})

            resp_cat = requests.get(category_url, headers=self.headers, timeout=self.timeout)
            cat_data = resp_cat.json().get("data", {}) if resp_cat.status_code == 200 else {}

            subcat_charts = {}
            if include_subcategories:
                subcategories = ["cli-agent", "ide-extension", "cloud-agent", "programming-app"]
                for sub in subcategories:
                    sub_url = f"{chart_url}&subcategory={sub}"
                    try:
                        sub_resp = requests.get(sub_url, headers=self.headers, timeout=self.timeout)
                        if sub_resp.status_code == 200:
                            subcat_charts[sub] = sub_resp.json().get("data", {})
                    except Exception as sub_err:
                        logging.warning("Failed to fetch subcategory %s: %s", sub, sub_err)

            return {
                "status": "ok",
                "data": {
                    "history_chart": {
                        "all": chart_data,
                        "subcategories": subcat_charts
                    },
                    "leaderboard": cat_data.get("apps", []),
                    "metadata": {
                        "group": "coding",
                        "subcategories": cat_data.get("subcategories", [])
                    }
                },
                "error": None
            }
        except Exception as e:
            logging.warning("Exception fetching coding apps: %s", e)
            return {"status": "error", "data": {}, "error": str(e)}

OpenRouterFrontendClient = OpenRouterWebCrawler
