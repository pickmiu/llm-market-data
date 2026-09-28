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
        requires_auth: bool = False
    ) -> Dict[str, Any]:
        """Makes an HTTP GET request with pacing, retry logic, and error handling."""
        if requires_auth and not self.api_key:
            raise OpenRouterAPIError("OPENROUTER_API_KEY is required for this endpoint")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {"User-Agent": self.user_agent}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        backoff_delays = [5.0, 10.0, 20.0]

        for attempt in range(self.max_retries):
            self._apply_rate_pacing()
            try:
                resp = requests.get(url, headers=headers, params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code in (429, 500, 502, 503, 504):
                    if attempt < self.max_retries - 1:
                        sleep_time = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                        time.sleep(sleep_time)
                        continue
                    else:
                        raise OpenRouterAPIError(
                            f"Max retries exceeded for {url}. Status code: {resp.status_code}"
                        )
                else:
                    raise OpenRouterAPIError(
                        f"Request failed with status {resp.status_code}: {resp.text}"
                    )
            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    sleep_time = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                    time.sleep(sleep_time)
                else:
                    raise OpenRouterAPIError(f"Network error calling {url}: {e}")

        raise OpenRouterAPIError(f"Max retries exceeded calling {url}")

    def get_models(self) -> Dict[str, Any]:
        """Fetches complete model list and metadata (/models). No auth required."""
        return self._request("models", requires_auth=False)

    def get_rankings_daily(
        self,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetches daily ranking dataset. Supports date=YYYY-MM-DD or start_date/end_date range."""
        params = {}
        if date:
            params["date"] = date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        return self._request("datasets/rankings-daily", params=params, requires_auth=True)
