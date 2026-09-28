import pytest
from unittest.mock import patch, MagicMock
from sources.openrouter.client import OpenRouterClient, OpenRouterAPIError

def test_client_init_defaults():
    client = OpenRouterClient()
    assert client.base_url == "https://openrouter.ai/api/v1"
    assert client.rate_delay == 2.5
    assert client.max_retries == 3
    assert client.timeout == 30

@patch("sources.openrouter.client.requests.get")
def test_get_models_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": [{"id": "openai/gpt-4o", "name": "GPT-4o"}]}
    mock_get.return_value = mock_resp

    client = OpenRouterClient(rate_delay=0.0)
    res = client.get_models()
    assert len(res["data"]) == 1
    assert res["data"][0]["id"] == "openai/gpt-4o"
    mock_get.assert_called_once_with(
        "https://openrouter.ai/api/v1/models",
        headers={"User-Agent": "LLM-Market-Data-Collector/1.0"},
        params=None,
        timeout=30
    )

@patch("sources.openrouter.client.requests.get")
def test_get_models_requires_no_auth(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": []}
    mock_get.return_value = mock_resp

    client = OpenRouterClient(api_key=None, rate_delay=0.0)
    client.get_models()
    assert "Authorization" not in mock_get.call_args[1]["headers"]

def test_get_rankings_daily_requires_auth():
    client = OpenRouterClient(api_key=None)
    with pytest.raises(OpenRouterAPIError, match="OPENROUTER_API_KEY is required"):
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
    res = client.get_rankings_daily(date="2026-09-27")
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

@patch("sources.openrouter.client.requests.get")
def test_get_rankings_daily_date_range(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {"date": "2025-01-01", "model_permaslug": "openai/gpt-4o", "total_tokens": 500},
            {"date": "2025-01-02", "model_permaslug": "openai/gpt-4o", "total_tokens": 600}
        ],
        "asOf": "2026-09-28T00:15:00Z"
    }
    mock_get.return_value = mock_resp

    client = OpenRouterClient(api_key="sk-test-key", rate_delay=0.0)
    res = client.get_rankings_daily(start_date="2025-01-01", end_date="2025-01-02")
    assert len(res["data"]) == 2
    mock_get.assert_called_once_with(
        "https://openrouter.ai/api/v1/datasets/rankings-daily",
        headers={
            "User-Agent": "LLM-Market-Data-Collector/1.0",
            "Authorization": "Bearer sk-test-key"
        },
        params={"start_date": "2025-01-01", "end_date": "2025-01-02"},
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
    res = client.get_rankings_daily(date="2026-09-27")
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
        client.get_rankings_daily(date="2026-09-27")
