import json
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from sources.openrouter.client import OpenRouterClient, OpenRouterAPIError
from sources.openrouter.crawler import OpenRouterWebCrawler

DATASET_INCEPTION_DATE = "2025-01-01"

def is_valid_json_file(file_path: Path) -> bool:
    """Checks whether file exists, has content > 0 bytes, and contains valid JSON."""
    if not file_path.exists() or file_path.stat().st_size == 0:
        return False
    try:
        with file_path.open("r", encoding="utf-8") as f:
            json.load(f)
        return True
    except Exception:
        return False

def find_missing_dates(
    rankings_dir: Path,
    start_date: datetime.date,
    end_date: datetime.date
) -> List[str]:
    """Scans date range and returns missing/invalid dates in reverse order (newest first)."""
    rankings_dir.mkdir(parents=True, exist_ok=True)
    missing = []
    curr = end_date
    while curr >= start_date:
        date_str = curr.strftime("%Y-%m-%d")
        file_path = rankings_dir / f"{date_str}.json"
        if not is_valid_json_file(file_path):
            missing.append(date_str)
        curr -= datetime.timedelta(days=1)
    return missing

def group_dates_into_ranges(dates: List[str], max_span_days: int = 30) -> List[Tuple[str, str]]:
    """Groups date strings into contiguous or bounded date ranges [start_date, end_date].
    Preserves input direction (e.g. newest-first if dates are descending)."""
    if not dates:
        return []

    ranges = []
    chunk = [dates[0]]
    prev_dt = datetime.datetime.strptime(dates[0], "%Y-%m-%d").date()

    for d_str in dates[1:]:
        curr_dt = datetime.datetime.strptime(d_str, "%Y-%m-%d").date()
        day_diff = abs((curr_dt - prev_dt).days)
        first_dt = datetime.datetime.strptime(chunk[0], "%Y-%m-%d").date()
        span = abs((curr_dt - first_dt).days) + 1

        if day_diff > 1 or span > max_span_days:
            chunk_sorted = sorted(chunk)
            ranges.append((chunk_sorted[0], chunk_sorted[-1]))
            chunk = [d_str]
        else:
            chunk.append(d_str)
        prev_dt = curr_dt

    if chunk:
        chunk_sorted = sorted(chunk)
        ranges.append((chunk_sorted[0], chunk_sorted[-1]))

    return ranges

def sync_models(
    client: OpenRouterClient,
    data_dir: Path,
    target_date: str,
    force: bool = False
) -> Path:
    """Fetches and persists OpenRouter model metadata and pricing snapshot."""
    models_dir = data_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    out_file = models_dir / f"{target_date}.json"

    if not force and is_valid_json_file(out_file):
        return out_file

    payload = client.get_models()
    snapshot = {
        "date": target_date,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "data": payload.get("data", [])
    }
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    return out_file

def sync_apps(
    crawler: OpenRouterWebCrawler,
    data_dir: Path,
    target_date: str,
    force: bool = False
) -> Path:
    """Fetches and persists OpenRouter frontend Apps & Coding Agents leaderboard snapshot."""
    apps_dir = data_dir / "apps"
    apps_dir.mkdir(parents=True, exist_ok=True)
    out_file = apps_dir / f"{target_date}.json"

    if not force and is_valid_json_file(out_file):
        return out_file

    fetch_res = crawler.fetch_apps()
    snapshot = {
        "date": target_date,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": fetch_res.get("status"),
        "error": fetch_res.get("error"),
        "data": fetch_res.get("data", {})
    }
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    return out_file

def sync_task_spend(
    crawler: OpenRouterWebCrawler,
    data_dir: Path,
    target_date: str,
    force: bool = False
) -> Path:
    """Fetches and persists OpenRouter frontend Top Models by Task spend snapshot."""
    task_dir = data_dir / "task_spend"
    task_dir.mkdir(parents=True, exist_ok=True)
    out_file = task_dir / f"{target_date}.json"

    if not force and is_valid_json_file(out_file):
        return out_file

    fetch_res = crawler.fetch_task_spend()
    snapshot = {
        "date": target_date,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": fetch_res.get("status"),
        "error": fetch_res.get("error"),
        "data": fetch_res.get("data", {})
    }
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    return out_file

def sync_session_cost(
    crawler: OpenRouterWebCrawler,
    data_dir: Path,
    target_date: str,
    force: bool = False
) -> Path:
    """Fetches and persists OpenRouter frontend Cost per session snapshot."""
    sc_dir = data_dir / "session_cost"
    sc_dir.mkdir(parents=True, exist_ok=True)
    out_file = sc_dir / f"{target_date}.json"

    if not force and is_valid_json_file(out_file):
        return out_file

    fetch_res = crawler.fetch_session_cost()
    snapshot = {
        "date": target_date,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": fetch_res.get("status"),
        "error": fetch_res.get("error"),
        "data": fetch_res.get("data", {})
    }
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    return out_file

def sync_benchmarks(
    crawler: OpenRouterWebCrawler,
    data_dir: Path,
    target_date: str,
    force: bool = False
) -> Path:
    """Fetches and persists OpenRouter frontend Benchmarks snapshot."""
    bm_dir = data_dir / "benchmarks"
    bm_dir.mkdir(parents=True, exist_ok=True)
    out_file = bm_dir / f"{target_date}.json"

    if not force and is_valid_json_file(out_file):
        return out_file

    fetch_res = crawler.fetch_benchmarks()
    snapshot = {
        "date": target_date,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": fetch_res.get("status"),
        "error": fetch_res.get("error"),
        "data": fetch_res.get("data", {})
    }
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    return out_file

def sync_performance(
    crawler: OpenRouterWebCrawler,
    data_dir: Path,
    target_date: str,
    force: bool = False
) -> Path:
    """Fetches and persists OpenRouter frontend Fastest models (performance) snapshot."""
    perf_dir = data_dir / "performance"
    perf_dir.mkdir(parents=True, exist_ok=True)
    out_file = perf_dir / f"{target_date}.json"

    if not force and is_valid_json_file(out_file):
        return out_file

    fetch_res = crawler.fetch_performance()
    snapshot = {
        "date": target_date,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": fetch_res.get("status"),
        "error": fetch_res.get("error"),
        "data": fetch_res.get("data", [])
    }
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    return out_file

def sync_rankings_daily(
    client: OpenRouterClient,
    data_dir: Path,
    missing_dates: List[str],
    max_requests: int = 40,
    force: bool = False,
    chunk_size: int = 30
) -> Dict[str, Any]:
    """Groups missing dates into range chunks and backfills rankings_daily within max_requests."""
    rankings_dir = data_dir / "rankings_daily"
    rankings_dir.mkdir(parents=True, exist_ok=True)

    date_ranges = group_dates_into_ranges(missing_dates, max_span_days=chunk_size)
    requests_made = 0
    fetched_days = 0
    failed = []

    for start_d, end_d in date_ranges:
        if requests_made >= max_requests:
            break

        try:
            res = client.get_rankings_daily(start_date=start_d, end_date=end_d)
            records = res.get("data", [])
            as_of = res.get("asOf")

            # Group returned rows by date
            by_date: Dict[str, List[Dict[str, Any]]] = {}
            for row in records:
                r_date = row.get("date")
                if r_date:
                    by_date.setdefault(r_date, []).append(row)

            # Determine all dates spanned by this chunk
            s_dt = datetime.datetime.strptime(start_d, "%Y-%m-%d").date()
            e_dt = datetime.datetime.strptime(end_d, "%Y-%m-%d").date()
            curr = s_dt
            while curr <= e_dt:
                d_str = curr.strftime("%Y-%m-%d")
                out_file = rankings_dir / f"{d_str}.json"
                if force or not is_valid_json_file(out_file):
                    day_snapshot = {
                        "date": d_str,
                        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "as_of": as_of,
                        "data": by_date.get(d_str, [])
                    }
                    with out_file.open("w", encoding="utf-8") as f:
                        json.dump(day_snapshot, f, indent=2, ensure_ascii=False)
                    fetched_days += 1
                curr += datetime.timedelta(days=1)

            requests_made += 1
        except OpenRouterAPIError as exc:
            failed.append({"range": f"{start_d}..{end_d}", "error": str(exc)})
            break

    remaining_days = max(0, len(missing_dates) - fetched_days)
    return {
        "requests_made": requests_made,
        "fetched_days": fetched_days,
        "remaining_days": remaining_days,
        "failed": failed
    }

def run_sync(
    data_dir: Path,
    api_key: Optional[str] = None,
    lookback_days: Optional[int] = None,
    max_requests: int = 40,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    force: bool = False,
    only: Optional[str] = None
) -> Dict[str, Any]:
    """Orchestrates sync pipeline across models, apps, task_spend, session_cost, benchmarks, performance, and rankings_daily."""
    today_utc = datetime.datetime.now(datetime.timezone.utc).date()
    yesterday_utc = today_utc - datetime.timedelta(days=1)
    today_str = today_utc.strftime("%Y-%m-%d")

    client = OpenRouterClient(api_key=api_key)
    crawler = OpenRouterWebCrawler()
    results = {}

    # 1. Sync models (API)
    if only in (None, "models"):
        models_file = sync_models(client, data_dir, today_str, force=force)
        results["models"] = str(models_file)

    # 2. Sync apps & coding agents (Frontend API)
    if only in (None, "apps"):
        apps_file = sync_apps(crawler, data_dir, today_str, force=force)
        results["apps"] = str(apps_file)

    # 3. Sync top models by task (Frontend API)
    if only in (None, "task_spend"):
        task_file = sync_task_spend(crawler, data_dir, today_str, force=force)
        results["task_spend"] = str(task_file)

    # 4. Sync cost per session (Frontend API)
    if only in (None, "session_cost"):
        session_cost_file = sync_session_cost(crawler, data_dir, today_str, force=force)
        results["session_cost"] = str(session_cost_file)

    # 5. Sync benchmarks (Frontend API)
    if only in (None, "benchmarks"):
        benchmarks_file = sync_benchmarks(crawler, data_dir, today_str, force=force)
        results["benchmarks"] = str(benchmarks_file)

    # 6. Sync performance (Frontend API)
    if only in (None, "performance"):
        perf_file = sync_performance(crawler, data_dir, today_str, force=force)
        results["performance"] = str(perf_file)

    # 7. Sync rankings daily (API)
    if only in (None, "rankings"):
        if end_date:
            e_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            e_dt = yesterday_utc

        if start_date:
            s_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        elif lookback_days is not None:
            s_dt = e_dt - datetime.timedelta(days=lookback_days - 1)
        else:
            # Auto-backfill to platform inception floor
            s_dt = datetime.datetime.strptime(DATASET_INCEPTION_DATE, "%Y-%m-%d").date()

        rankings_dir = data_dir / "rankings_daily"
        missing = find_missing_dates(rankings_dir, s_dt, e_dt)
        rankings_stats = sync_rankings_daily(
            client=client,
            data_dir=data_dir,
            missing_dates=missing,
            max_requests=max_requests,
            force=force
        )
        results["rankings_daily"] = rankings_stats

    return results
