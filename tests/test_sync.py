import json
import datetime
from pathlib import Path
from unittest.mock import MagicMock
from sources.openrouter.sync import (
    find_missing_dates,
    sync_models,
    sync_apps,
    sync_task_spend,
    sync_session_cost,
    sync_benchmarks,
    sync_performance,
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

def test_group_dates_into_ranges():
    from sources.openrouter.sync import group_dates_into_ranges
    dates = ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-10", "2025-01-11"]
    ranges = group_dates_into_ranges(dates, max_span_days=5)
    assert ranges == [("2025-01-01", "2025-01-03"), ("2025-01-10", "2025-01-11")]

def test_sync_apps_saves_file(tmp_path):
    crawler = MagicMock()
    crawler.fetch_apps.return_value = {
        "status": "ok",
        "data": {"day": [{"title": "Hermes Agent", "rank": 2}]}
    }
    out_file = sync_apps(crawler, tmp_path, target_date="2026-09-28")
    assert out_file.exists()
    content = json.loads(out_file.read_text())
    assert content["date"] == "2026-09-28"
    assert content["data"]["day"][0]["title"] == "Hermes Agent"

def test_sync_task_spend_saves_file(tmp_path):
    crawler = MagicMock()
    crawler.fetch_task_spend.return_value = {
        "status": "ok",
        "data": {"macroCategories": [{"name": "General", "share": 0.312}]}
    }
    out_file = sync_task_spend(crawler, tmp_path, target_date="2026-09-28")
    assert out_file.exists()
    content = json.loads(out_file.read_text())
    assert content["date"] == "2026-09-28"
    assert content["data"]["macroCategories"][0]["name"] == "General"

def test_sync_session_cost_saves_file(tmp_path):
    crawler = MagicMock()
    crawler.fetch_session_cost.return_value = {
        "status": "ok",
        "data": {"harnesses": [{"appId": 3067167}]}
    }
    out_file = sync_session_cost(crawler, tmp_path, target_date="2026-09-28")
    assert out_file.exists()
    content = json.loads(out_file.read_text())
    assert content["date"] == "2026-09-28"
    assert content["data"]["harnesses"][0]["appId"] == 3067167

def test_sync_benchmarks_saves_file(tmp_path):
    crawler = MagicMock()
    crawler.fetch_benchmarks.return_value = {
        "status": "ok",
        "data": {"aaData": {"intelligence": [{"aa_name": "Claude Opus 5.5", "score": 57.6}]}}
    }
    out_file = sync_benchmarks(crawler, tmp_path, target_date="2026-09-28")
    assert out_file.exists()
    content = json.loads(out_file.read_text())
    assert content["date"] == "2026-09-28"
    assert content["data"]["aaData"]["intelligence"][0]["score"] == 57.6

def test_sync_performance_saves_file(tmp_path):
    crawler = MagicMock()
    crawler.fetch_performance.return_value = {
        "status": "ok",
        "data": [{"name": "gpt-oss-120b", "p50_throughput": 700}]
    }
    out_file = sync_performance(crawler, tmp_path, target_date="2026-09-28")
    assert out_file.exists()
    content = json.loads(out_file.read_text())
    assert content["date"] == "2026-09-28"
    assert content["data"][0]["name"] == "gpt-oss-120b"

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

def test_sync_rankings_daily_chunked_and_respects_max_requests(tmp_path):
    client = MagicMock()
    client.get_rankings_daily.side_effect = [
        {
            "data": [
                {"date": "2026-09-26", "model_permaslug": "openai/gpt-4o", "total_tokens": 100},
                {"date": "2026-09-27", "model_permaslug": "openai/gpt-4o", "total_tokens": 200}
            ],
            "asOf": "2026-09-28T00:00:00Z"
        },
        {
            "data": [
                {"date": "2026-09-24", "model_permaslug": "openai/gpt-4o", "total_tokens": 300},
                {"date": "2026-09-25", "model_permaslug": "openai/gpt-4o", "total_tokens": 400}
            ],
            "asOf": "2026-09-28T00:00:00Z"
        }
    ]

    missing_dates = ["2026-09-27", "2026-09-26", "2026-09-25", "2026-09-24"]
    stats = sync_rankings_daily(client, tmp_path, missing_dates, max_requests=1, chunk_size=2)

    assert stats["requests_made"] == 1
    assert stats["fetched_days"] == 2
    assert stats["remaining_days"] == 2
    assert client.get_rankings_daily.call_count == 1
    assert (tmp_path / "rankings_daily" / "2026-09-27.json").exists()
    assert (tmp_path / "rankings_daily" / "2026-09-26.json").exists()
    assert not (tmp_path / "rankings_daily" / "2026-09-25.json").exists()

def test_run_sync_selective(tmp_path):
    from unittest.mock import patch
    with patch("sources.openrouter.sync.OpenRouterClient") as mock_client_cls, \
         patch("sources.openrouter.sync.OpenRouterWebCrawler") as mock_crawler_cls:
        crawler = mock_crawler_cls.return_value
        crawler.fetch_performance.return_value = {"status": "ok", "data": []}

        res = run_sync(data_dir=tmp_path, only="performance")
        assert "performance" in res
        assert "models" not in res
        assert "rankings_daily" not in res
        assert (tmp_path / "performance").is_dir()

