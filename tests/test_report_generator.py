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
        if m["total_tokens"] > 0:
            assert pytest.approx(m["empirical_eff_p_per_m"], rel=1e-3) == (m["spend_usd"] / m["total_tokens"]) * 1e6
