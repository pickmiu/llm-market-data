from unittest.mock import patch, MagicMock
from sources.openrouter.crawler import OpenRouterWebCrawler

SAMPLE_APPS_PAYLOAD = {
    "day": [
        {
            "title": "Hermes Agent",
            "slug": "hermes-agent",
            "category": "cli-agent",
            "rank": 2,
            "tokens": 4016664947,
            "requests": 1500000
        }
    ]
}

SAMPLE_TASK_SPEND_PAYLOAD = {
    "macroCategories": [
        {
            "name": "General",
            "tokens": 450000000,
            "usd": 1250.5,
            "share": 0.312
        }
    ],
    "tasks": [
        {
            "name": "General Chat",
            "category": "General",
            "tokens": 200000000,
            "usd": 600.0,
            "share": 0.15
        }
    ],
    "models": [
        {
            "id": "anthropic/claude-3.5-sonnet",
            "taskShares": {"General Chat": 0.45}
        }
    ]
}

SAMPLE_SESSION_COST_PAYLOAD = {
    "harnesses": [
        {
            "appId": 3067167,
            "models": [
                {
                    "id": "openai/gpt-4o",
                    "points": [
                        {"bucket": "single", "medianUsd": 0.005},
                        {"bucket": "short", "medianUsd": 0.02},
                        {"bucket": "core", "medianUsd": 0.08},
                        {"bucket": "long", "medianUsd": 0.25}
                    ]
                }
            ]
        }
    ]
}

SAMPLE_BENCHMARKS_PAYLOAD = {
    "aaData": {
        "intelligence": [
            {
                "aa_name": "Claude Opus 5.5",
                "openrouter_name": "anthropic/claude-opus-5",
                "score": 57.6
            }
        ],
        "coding": [
            {
                "aa_name": "Claude Opus 5.5",
                "openrouter_name": "anthropic/claude-opus-5",
                "score": 68.2
            }
        ]
    },
    "weightedInputPrices": {
        "anthropic/claude-opus-5": 1.62
    }
}

SAMPLE_PERFORMANCE_PAYLOAD = [
    {
        "id": "openai/gpt-oss-120b",
        "name": "gpt-oss-120b",
        "p50_throughput": 700,
        "best_throughput_provider": "Cerebras",
        "best_throughput_price": 0.35,
        "p50_latency": 250,
        "best_latency_provider": "Cerebras",
        "best_latency_price": 0.35
    }
]

def test_crawler_init():
    crawler = OpenRouterWebCrawler()
    assert crawler.base_url == "https://openrouter.ai/api/frontend/v1/rankings"
    assert crawler.timeout == 20

@patch("sources.openrouter.crawler.requests.get")
def test_fetch_apps_success(mock_get):
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {"data": SAMPLE_APPS_PAYLOAD}
    mock_get.return_value = mock_resp

    crawler = OpenRouterWebCrawler()
    result = crawler.fetch_apps()

    assert result["status"] == "ok"
    assert result["data"]["day"][0]["title"] == "Hermes Agent"
    assert result["data"]["day"][0]["rank"] == 2
    mock_get.assert_called_once_with(
        "https://openrouter.ai/api/frontend/v1/rankings/apps",
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
        timeout=20
    )

@patch("sources.openrouter.crawler.requests.get")
def test_fetch_task_spend_success(mock_get):
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {"data": SAMPLE_TASK_SPEND_PAYLOAD}
    mock_get.return_value = mock_resp

    crawler = OpenRouterWebCrawler()
    result = crawler.fetch_task_spend()

    assert result["status"] == "ok"
    assert result["data"]["macroCategories"][0]["name"] == "General"
    assert result["data"]["macroCategories"][0]["share"] == 0.312

@patch("sources.openrouter.crawler.requests.get")
def test_fetch_session_cost_success(mock_get):
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {"data": SAMPLE_SESSION_COST_PAYLOAD}
    mock_get.return_value = mock_resp

    crawler = OpenRouterWebCrawler()
    result = crawler.fetch_session_cost()

    assert result["status"] == "ok"
    assert result["data"]["harnesses"][0]["appId"] == 3067167
    assert result["data"]["harnesses"][0]["models"][0]["points"][0]["bucket"] == "single"

@patch("sources.openrouter.crawler.requests.get")
def test_fetch_benchmarks_success(mock_get):
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {"data": SAMPLE_BENCHMARKS_PAYLOAD}
    mock_get.return_value = mock_resp

    crawler = OpenRouterWebCrawler()
    result = crawler.fetch_benchmarks()

    assert result["status"] == "ok"
    assert result["data"]["aaData"]["intelligence"][0]["score"] == 57.6
    assert result["data"]["weightedInputPrices"]["anthropic/claude-opus-5"] == 1.62

@patch("sources.openrouter.crawler.requests.get")
def test_fetch_performance_success(mock_get):
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {"data": SAMPLE_PERFORMANCE_PAYLOAD}
    mock_get.return_value = mock_resp

    crawler = OpenRouterWebCrawler()
    result = crawler.fetch_performance()

    assert result["status"] == "ok"
    assert len(result["data"]) == 1
    assert result["data"][0]["name"] == "gpt-oss-120b"
    assert result["data"][0]["p50_throughput"] == 700

@patch("sources.openrouter.crawler.requests.get")
def test_fetch_error_graceful(mock_get):
    mock_resp = MagicMock(status_code=500, text="Internal Error")
    mock_get.return_value = mock_resp

    crawler = OpenRouterWebCrawler()
    result = crawler.fetch_apps()

    assert result["status"] == "error"
    assert "500" in result["error"]
    assert result["data"] == {}

@patch("sources.openrouter.crawler.requests.get")
def test_fetch_transcription_from_ssr_flight(mock_get):
    flight_html = '''
    <html>
      <script>
      self.__next_f.push([1,"[{\\\"date\\\":\\\"2026-09-27\\\",\\\"model_permaslug\\\":\\\"openai/whisper-large-v3\\\",\\\"count\\\":8381036,\\\"change\\\":0.05},{\\\"date\\\":\\\"2026-09-27\\\",\\\"model_permaslug\\\":\\\"openai/whisper-large-v3-turbo\\\",\\\"count\\\":6680047,\\\"change\\\":0.31}]"])
      </script>
    </html>
    '''
    mock_resp = MagicMock(status_code=200, text=flight_html)
    mock_get.return_value = mock_resp

    crawler = OpenRouterWebCrawler()
    res = crawler.fetch_transcription()

    assert res["status"] == "ok"
    models = res["data"]["models"]
    assert len(models) == 2
    assert models[0]["model_permaslug"] == "openai/whisper-large-v3"
    assert models[0]["count"] == 8381036

@patch("sources.openrouter.crawler.requests.get")
def test_fetch_transcription_fallback_table(mock_get):
    table_html = '''
    <html>
      <table>
        <tr><th>Rank</th><th>Model</th><th>Author</th><th>Requests</th><th>Change</th></tr>
        <tr><td>1</td><td>Whisper Large V3</td><td>openai</td><td>8.38M requests</td><td>+5%</td></tr>
      </table>
    </html>
    '''
    mock_resp = MagicMock(status_code=200, text=table_html)
    mock_get.return_value = mock_resp

    crawler = OpenRouterWebCrawler()
    res = crawler.fetch_transcription()

    assert res["status"] == "ok"
    models = res["data"]["models"]
    assert len(models) == 1
    assert models[0]["rank"] == 1
    assert models[0]["name"] == "Whisper Large V3"
    assert models[0]["author"] == "openai"

@patch("sources.openrouter.crawler.requests.get")
def test_fetch_transcription_error(mock_get):
    mock_resp = MagicMock(status_code=500, text="Internal Error")
    mock_get.return_value = mock_resp

    crawler = OpenRouterWebCrawler()
    res = crawler.fetch_transcription()
    assert res["status"] == "error"
    assert "500" in res["error"]

@patch("sources.openrouter.crawler.requests.get")
def test_fetch_coding_apps_success(mock_get):
    chart_payload = {
        "status_code": 200,
        "data": {
            "chartData": [{"x": "2026-09-21", "ys": {"3067167": 7726723402818}}],
            "titleMap": {"3067167": "Hermes Agent"}
        }
    }
    cat_payload = {
        "status_code": 200,
        "data": {
            "apps": [{"rank": 1, "total_tokens": "1729210473166", "app": {"title": "Hermes Agent"}}],
            "subcategories": ["cli-agent", "ide-extension"]
        }
    }

    def side_effect(url, **kwargs):
        resp = MagicMock()
        if "category-chart" in url:
            resp.status_code = 200
            resp.json.return_value = chart_payload
        elif "category" in url:
            resp.status_code = 200
            resp.json.return_value = cat_payload
        else:
            resp.status_code = 404
        return resp

    mock_get.side_effect = side_effect

    crawler = OpenRouterWebCrawler()
    res = crawler.fetch_coding_apps(include_subcategories=True)

    assert res["status"] == "ok"
    assert len(res["data"]["history_chart"]["all"]["chartData"]) == 1
    assert "cli-agent" in res["data"]["history_chart"]["subcategories"]
    assert res["data"]["leaderboard"][0]["app"]["title"] == "Hermes Agent"

@patch("sources.openrouter.crawler.requests.get")
def test_fetch_coding_apps_error(mock_get):
    mock_resp = MagicMock(status_code=500, text="Internal Error")
    mock_get.return_value = mock_resp

    crawler = OpenRouterWebCrawler()
    res = crawler.fetch_coding_apps()
    assert res["status"] == "error"
    assert "500" in res["error"]

