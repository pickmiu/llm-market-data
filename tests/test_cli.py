from unittest.mock import patch
from cli import build_parser, main

def test_cli_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["sync"])
    assert args.command == "sync"
    assert args.lookback_days is None
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
        "--only", "apps"
    ])
    assert args.lookback_days == 30
    assert args.max_requests == 20
    assert args.start_date == "2026-08-01"
    assert args.end_date == "2026-08-31"
    assert args.force is True
    assert args.only == "apps"

@patch("cli.run_sync")
def test_cli_main_executes_sync(mock_run_sync):
    mock_run_sync.return_value = {
        "models": "data/openrouter/models/2026-09-28.json",
        "apps": "data/openrouter/apps/2026-09-28.json",
        "task_spend": "data/openrouter/task_spend/2026-09-28.json",
        "session_cost": "data/openrouter/session_cost/2026-09-28.json",
        "benchmarks": "data/openrouter/benchmarks/2026-09-28.json",
        "performance": "data/openrouter/performance/2026-09-28.json",
        "transcription": "data/openrouter/transcription/2026-09-28.json",
        "coding_apps": "data/openrouter/coding_apps/2026-09-28.json",
        "rankings_models": "data/openrouter/rankings_models/2026-09-28.json",
        "rankings_daily": {"fetched_days": 2, "remaining_days": 0, "failed": []}
    }
    exit_code = main(["sync", "--lookback-days", "7"])
    assert exit_code == 0
    mock_run_sync.assert_called_once()
