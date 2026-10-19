import pytest
from pathlib import Path
from report.generate_weekly_top5_report import ModelReportGenerator

def test_model_report_generator_snapshot_resolution():
    root = Path(__file__).resolve().parent.parent
    generator = ModelReportGenerator(project_root=root)

    # Test snapshot lookup
    models_file = generator._find_snapshot_file("models", "2026-10-11")
    assert models_file is not None
    assert models_file.exists()
    assert models_file.stem <= "2026-10-11"

    # Test 7-day model snapshot resolution
    items = generator.fetch_official_7day_models(target_date="2026-10-11")
    assert len(items) > 0
    # Must contain 2026-10-11 records
    assert any(r.get("date") == "2026-10-11 00:00:00" for r in items)

def test_model_report_generator_token_consistency():
    root = Path(__file__).resolve().parent.parent
    generator = ModelReportGenerator(project_root=root)
    generator._load_local_datasets(target_date="2026-10-12")

    items = generator.fetch_official_7day_models(target_date="2026-10-11")
    rolling_dates = [f"2026-10-{d:02d}" for d in range(5, 12)]
    top5_tokens, top5_spend = generator.compute_model_metrics(items, rolling_dates)

    assert len(top5_tokens) == 5
    assert len(top5_spend) == 5

    # Check that for all models, total_tokens == prompt_tokens + completion_tokens
    for m in top5_tokens + top5_spend:
        assert m["total_tokens"] == m["prompt_tokens"] + m["completion_tokens"]
        if m["completion_tokens"] > 0:
            assert pytest.approx(m["io_ratio"], rel=1e-3) == m["prompt_tokens"] / m["completion_tokens"]


def test_model_report_generator_spend_and_token_metrics():
    root = Path(__file__).resolve().parent.parent
    generator = ModelReportGenerator(project_root=root)
    generator._load_local_datasets(target_date="2026-10-19")

    # Fetch 2026-10-18 tokens and spend
    official_items = generator.fetch_official_7day_models(target_date="2026-10-18")
    spend_items = generator.fetch_official_7day_models_spend(target_date="2026-10-18")
    assert len(spend_items) > 0

    rolling_dates = [f"2026-10-{d:02d}" for d in range(12, 19)]
    top5_tokens, top5_spend = generator.compute_model_metrics(
        official_items, rolling_dates, spend_items=spend_items
    )

    assert len(top5_tokens) == 5
    assert len(top5_spend) == 5

    # Check top 1 spend is Claude Opus 5.5 and has positive spend share
    top_spend_model = top5_spend[0]
    assert "claude-opus" in top_spend_model["slug"]
    assert top_spend_model["spend_share_pct"] > 10.0

    # Verify vendor metrics
    top_vendors = generator.compute_vendor_metrics(spend_items, official_items)
    assert len(top_vendors) >= 5
    assert top_vendors[0]["vendor"] == "Anthropic"
    assert top_vendors[0]["spend_share_pct"] > 30.0
    assert top_vendors[1]["vendor"] == "OpenAI"
    assert sum(v["spend_share_pct"] for v in top_vendors[:5]) > 80.0


