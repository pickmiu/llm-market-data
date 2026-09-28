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
    env_lookback = os.getenv("LOOKBACK_DAYS")
    sync_parser.add_argument(
        "--lookback-days",
        type=int,
        default=int(env_lookback) if env_lookback else None,
        help="Optional: Number of past days to scan. If omitted, automatically backfills to platform inception (2025-01-01)."
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
        choices=["models", "rankings", "apps", "task_spend", "session_cost", "benchmarks", "performance"],
        default=None,
        help="Sync only specified target (models, rankings, apps, task_spend, session_cost, benchmarks, or performance)"
    )

    return parser

def main(args: list = None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(args)

    if parsed.command == "sync":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key and parsed.only not in ("models", "apps", "task_spend", "session_cost", "benchmarks", "performance"):
            print("[Warning] OPENROUTER_API_KEY is not set. Rankings daily API calls will fail.")

        data_dir = Path(__file__).resolve().parent / "data" / "openrouter"

        print(f"[*] Starting OpenRouter sync (lookback: {parsed.lookback_days}, max_requests: {parsed.max_requests})...")
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
            if "apps" in results:
                print(f"  - Apps snapshot: {results['apps']}")
            if "task_spend" in results:
                print(f"  - Top models by task snapshot: {results['task_spend']}")
            if "session_cost" in results:
                print(f"  - Cost per session snapshot: {results['session_cost']}")
            if "benchmarks" in results:
                print(f"  - Benchmarks snapshot: {results['benchmarks']}")
            if "performance" in results:
                print(f"  - Performance snapshot: {results['performance']}")
            if "rankings_daily" in results:
                stats = results["rankings_daily"]
                print(f"  - Daily rankings: fetched {stats['fetched_days']} days, remaining missing {stats['remaining_days']} days")
                if stats["failed"]:
                    print(f"  - Failed items: {stats['failed']}")
            return 0
        except Exception as exc:
            print(f"[!] Sync failed: {exc}", file=sys.stderr)
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
