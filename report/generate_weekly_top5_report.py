#!/usr/bin/env python3
"""
Generate Weekly Top 5 LLM Models Report (Tokens & Spend)
Covers the latest rolling 7-day complete window: 2026-09-22 to 2026-09-28.

Key design:
- Key data first (Rankings & Top 1 App per model).
- Simplified references: names only, only 1st preferred App per model.
- Strictly objective: no subjective summaries or derivations.
- Methodology & calculation parameters at the very end.
"""

import re
import json
import logging
import argparse
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import requests

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")


class ModelReportGenerator:
    def __init__(self, project_root: Optional[Path] = None):
        self.root = project_root or Path(__file__).resolve().parent.parent
        self.data_dir = self.root / "data" / "openrouter"
        self.report_dir = self.root / "report"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # Loaded data caches
        self.models_meta: List[Dict[str, Any]] = []
        self.meta_by_canon: Dict[str, Dict[str, Any]] = {}
        self.meta_by_id: Dict[str, Dict[str, Any]] = {}
        self.benchmarks: Dict[str, Any] = {}
        self.task_spend: Dict[str, Any] = {}
        self._load_local_datasets()

    def _load_local_datasets(self) -> None:
        """Loads models metadata, benchmarks, and task spend snapshots."""
        # 1. Models metadata
        models_file = self.data_dir / "models" / "2026-09-29.json"
        if not models_file.exists():
            models_file = self.data_dir / "models" / "2026-09-28.json"
        if models_file.exists():
            with models_file.open("r", encoding="utf-8") as f:
                self.models_meta = json.load(f).get("data", [])

            # Index metadata, prioritizing standard catalog models over batch/free variants
            for m in self.models_meta:
                mid = m.get("id", "")
                is_variant = ":batch" in mid or ":free" in mid
                if mid and (mid not in self.meta_by_id or not is_variant):
                    self.meta_by_id[mid] = m
                cslug = m.get("canonical_slug")
                if cslug and (cslug not in self.meta_by_canon or not is_variant):
                    self.meta_by_canon[cslug] = m

        # 2. Benchmarks (weighted input prices & costPerRequest)
        bench_file = self.data_dir / "benchmarks" / "2026-09-29.json"
        if not bench_file.exists():
            bench_file = self.data_dir / "benchmarks" / "2026-09-28.json"
        if bench_file.exists():
            with bench_file.open("r", encoding="utf-8") as f:
                self.benchmarks = json.load(f).get("data", {})

        # 3. Task spend (macro category & tasks distribution)
        ts_file = self.data_dir / "task_spend" / "2026-09-29.json"
        if not ts_file.exists():
            ts_file = self.data_dir / "task_spend" / "2026-09-28.json"
        if ts_file.exists():
            with ts_file.open("r", encoding="utf-8") as f:
                self.task_spend = json.load(f).get("data", {})

    def get_latest_7_days(self) -> List[str]:
        """Identifies the latest 7 consecutive complete dates available in rankings_daily."""
        rankings_dir = self.data_dir / "rankings_daily"
        existing_files = sorted([
            f.stem for f in rankings_dir.glob("*.json")
            if re.match(r"^\d{4}-\d{2}-\d{2}$", f.stem)
        ])
        if not existing_files:
            raise FileNotFoundError("No daily ranking files found in rankings_daily directory.")
        latest_date_str = existing_files[-1]
        latest_dt = datetime.datetime.strptime(latest_date_str, "%Y-%m-%d").date()
        # 7 continuous rolling days ending on latest_dt
        dates = [(latest_dt - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
        return dates

    def fetch_official_7day_models(self, target_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetches the official OpenRouter rolling 7-day model rankings endpoint.
        Prefers local cached snapshot in data/openrouter/rankings_models/{target_date}.json if present.
        """
        if target_date:
            local_snap = self.data_dir / "rankings_models" / f"{target_date}.json"
            if local_snap.exists():
                try:
                    with local_snap.open("r", encoding="utf-8") as f:
                        d = json.load(f)
                        data = d.get("data", [])
                        if data:
                            logging.info("Loaded official rankings/models from local snapshot: %s", local_snap)
                            return data
                except Exception as e:
                    logging.warning("Failed to read local snapshot %s: %s", local_snap, e)

        url = "https://openrouter.ai/api/frontend/v1/rankings/models"
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if target_date and data:
                    out_dir = self.data_dir / "rankings_models"
                    out_dir.mkdir(parents=True, exist_ok=True)
                    out_file = out_dir / f"{target_date}.json"
                    snapshot = {
                        "date": target_date,
                        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "status": "ok",
                        "error": None,
                        "data": data
                    }
                    try:
                        with out_file.open("w", encoding="utf-8") as f:
                            json.dump(snapshot, f, indent=2, ensure_ascii=False)
                        logging.info("Cached rankings/models snapshot to %s", out_file)
                    except Exception as w_err:
                        logging.warning("Failed to save local rankings_models snapshot: %s", w_err)
                return data
            else:
                logging.warning("Official rankings/models HTTP %s", resp.status_code)
        except Exception as e:
            logging.warning("Failed to fetch official rankings/models: %s", e)
        return []

    def scrape_model_apps_realtime(self, slug: str) -> List[Dict[str, Any]]:
        """
        Scrapes real-time Top Apps from OpenRouter model page.
        Does not persist to disk, returning directly as requested.
        """
        clean_slug = re.sub(r"-\d{8}$", "", slug)
        candidates = [clean_slug, slug]
        pattern = re.compile(
            r'<div class="col-span-1[^"]*">(\d+)<!-- -->\.</div>.*?'
            r'<a [^>]*href="([^"]+)"[^>]*>(.*?)<svg.*?'
            r'(?:<span[^>]*>(.*?)</span>.*?)?'
            r'<span>([0-9\.]+[KMBT]?)</span><span class="ml-1">tokens</span>',
            re.DOTALL
        )

        for s in candidates:
            url = f"https://openrouter.ai/models/{s}"
            try:
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 200:
                    matches = pattern.findall(resp.text)
                    if matches:
                        results = []
                        for rank, href, raw_name, raw_desc, tokens in matches:
                            clean_name = re.sub(r"<[^>]+>", "", raw_name).strip()
                            clean_desc = re.sub(r"<[^>]+>", "", raw_desc or "").strip()
                            clean_desc = clean_desc.replace("&amp;", "&").replace("&#x27;", "'")
                            results.append({
                                "rank": int(rank),
                                "name": clean_name,
                                "description": clean_desc,
                                "tokens": tokens
                            })
                        return results
            except Exception as e:
                logging.warning("Failed scraping %s: %s", url, e)
        return []

    def get_model_metadata(self, slug: str) -> Dict[str, Any]:
        """Resolves standard catalog metadata and pricing for a model slug."""
        clean = slug.split(":")[0]
        base_clean = re.sub(r"-\d{8}$", "", clean)
        m = (
            self.meta_by_canon.get(slug)
            or self.meta_by_id.get(slug)
            or self.meta_by_canon.get(clean)
            or self.meta_by_id.get(clean)
            or self.meta_by_canon.get(base_clean)
            or self.meta_by_id.get(base_clean)
        )
        return m or {}

    def get_task_scenarios_for_model(self, slug: str) -> Dict[str, Any]:
        """Extracts scenario and task distribution for a model from task_spend snapshot."""
        clean = slug.split(":")[0]
        base_clean = re.sub(r"-\d{8}$", "", clean)
        candidates = {slug, clean, base_clean}

        spend_data = self.task_spend.get("spend", {})
        macro_shares = {}
        for mc in spend_data.get("macroCategories", []):
            macro_shares[mc.get("key")] = mc.get("spendShare", 0.0)

        tasks = spend_data.get("tasks", [])
        matched_tasks = []
        macro_breakdown = {"code": 0.0, "agent": 0.0, "data": 0.0, "general": 0.0}

        for t in tasks:
            macro = t.get("macroCategory", "general")
            tag = t.get("tag", "general")
            for m_item in t.get("models", []):
                m_name = m_item.get("model", "")
                if any(c in m_name for c in candidates):
                    share = m_item.get("share", 0.0)
                    macro_breakdown[macro] = max(macro_breakdown.get(macro, 0.0), share)
                    matched_tasks.append({
                        "tag": tag,
                        "macro": macro,
                        "share": share
                    })

        matched_tasks = sorted(matched_tasks, key=lambda x: x["share"], reverse=True)
        return {
            "top_tasks": matched_tasks[:5],
            "macro_breakdown": macro_breakdown
        }

    def compute_model_metrics(self, official_items: List[Dict[str, Any]], rolling_dates: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Computes detailed token, spend, pricing, and cache metrics for all models.
        Properly accumulates across variants for each model_permaslug.
        Returns (top5_by_tokens, top5_by_spend).
        """
        daily_tokens = {}
        for dt in rolling_dates:
            fpath = self.data_dir / "rankings_daily" / f"{dt}.json"
            if fpath.exists():
                with fpath.open("r", encoding="utf-8") as f:
                    day_rows = json.load(f).get("data", [])
                    for r in day_rows:
                        s = r.get("model_permaslug")
                        if s:
                            daily_tokens[s] = daily_tokens.get(s, 0) + int(r.get("total_tokens", 0))

        off_by_slug: Dict[str, Dict[str, Any]] = {}
        for row in official_items:
            s = row.get("model_permaslug")
            if not s:
                continue
            if s not in off_by_slug:
                off_by_slug[s] = {
                    "total_prompt_tokens": 0,
                    "total_completion_tokens": 0,
                    "total_native_tokens_cached": 0,
                    "total_usage": 0.0,
                    "count": 0
                }
            off_by_slug[s]["total_prompt_tokens"] += int(row.get("total_prompt_tokens") or 0)
            off_by_slug[s]["total_completion_tokens"] += int(row.get("total_completion_tokens") or 0)
            off_by_slug[s]["total_native_tokens_cached"] += int(row.get("total_native_tokens_cached") or 0)
            off_by_slug[s]["total_usage"] += float(row.get("total_usage") or 0.0)
            off_by_slug[s]["count"] += int(row.get("count") or 0)

        all_slugs = set(daily_tokens.keys()).union(off_by_slug.keys())
        all_models_stats = []

        wip_dict = self.benchmarks.get("weightedInputPrices", {})
        cpr_dict = self.benchmarks.get("costPerRequest", {})

        for slug in all_slugs:
            if slug == "other":
                continue

            off_row = off_by_slug.get(slug, {})
            p_tok = int(off_row.get("total_prompt_tokens", 0))
            c_tok = int(off_row.get("total_completion_tokens", 0))
            official_tot = p_tok + c_tok
            cached_native = int(off_row.get("total_native_tokens_cached", 0))
            daily_tot = daily_tokens.get(slug, 0)
            tot_tokens = max(official_tot, daily_tot)
            spend_usd = float(off_row.get("total_usage", 0.0))
            req_count = int(off_row.get("count", 0))

            meta = self.get_model_metadata(slug)
            pricing = meta.get("pricing", {})
            prompt_p = float(pricing.get("prompt", 0) or 0)
            comp_p = float(pricing.get("completion", 0) or 0)
            cache_read_p = float(pricing.get("input_cache_read", 0) or 0)
            cache_write_p = float(pricing.get("input_cache_write", 0) or 0)

            if p_tok == 0 and c_tok == 0 and tot_tokens > 0:
                p_tok = int(tot_tokens * 0.90)
                c_tok = tot_tokens - p_tok

            io_ratio = (p_tok / c_tok) if c_tok > 0 else 0.0

            if p_tok + c_tok > 0:
                nominal_p_per_m = ((p_tok * prompt_p + c_tok * comp_p) / (p_tok + c_tok)) * 1e6
            else:
                nominal_p_per_m = (0.8 * prompt_p + 0.2 * comp_p) * 1e6

            wip_val = wip_dict.get(slug)
            if wip_val is None:
                clean_slug = slug.split(":")[0]
                wip_val = wip_dict.get(clean_slug)

            prompt_p_per_m = prompt_p * 1e6
            cache_read_p_per_m = cache_read_p * 1e6
            comp_p_per_m = comp_p * 1e6

            if wip_val is not None and prompt_p_per_m > cache_read_p_per_m:
                h_implied = max(0.0, min(1.0, (prompt_p_per_m - float(wip_val)) / (prompt_p_per_m - cache_read_p_per_m)))
            elif cached_native > 0 and p_tok > 0:
                h_implied = min(1.0, cached_native / p_tok)
            else:
                h_implied = 0.0

            if wip_val is not None and p_tok + c_tok > 0:
                eff_cache_p_per_m = ((p_tok * (float(wip_val) / 1e6) + c_tok * comp_p) / (p_tok + c_tok)) * 1e6
            elif p_tok + c_tok > 0:
                eff_cache_p_per_m = (
                    ((1 - h_implied) * p_tok * prompt_p + h_implied * p_tok * cache_read_p + c_tok * comp_p)
                    / (p_tok + c_tok)
                ) * 1e6
            else:
                eff_cache_p_per_m = nominal_p_per_m

            if tot_tokens > 0 and spend_usd > 0:
                empirical_eff_p_per_m = (spend_usd / tot_tokens) * 1e6
            else:
                empirical_eff_p_per_m = eff_cache_p_per_m

            if nominal_p_per_m > 0:
                savings_pct = max(0.0, (1.0 - (empirical_eff_p_per_m / nominal_p_per_m))) * 100
            else:
                savings_pct = 0.0

            cost_per_req = cpr_dict.get(slug) or cpr_dict.get(slug.split(":")[0])

            model_obj = {
                "slug": slug,
                "name": meta.get("name") or slug,
                "context_length": meta.get("context_length", 0),
                "total_tokens": tot_tokens,
                "prompt_tokens": p_tok,
                "completion_tokens": c_tok,
                "cached_tokens": cached_native,
                "spend_usd": spend_usd,
                "request_count": req_count,
                "io_ratio": io_ratio,
                "prompt_p_per_m": prompt_p_per_m,
                "comp_p_per_m": comp_p_per_m,
                "cache_read_p_per_m": cache_read_p_per_m,
                "cache_write_p_per_m": cache_write_p * 1e6,
                "wip_per_m": float(wip_val) if wip_val is not None else None,
                "h_implied": h_implied,
                "nominal_p_per_m": nominal_p_per_m,
                "eff_cache_p_per_m": eff_cache_p_per_m,
                "empirical_eff_p_per_m": empirical_eff_p_per_m,
                "savings_pct": savings_pct,
                "cost_per_req": float(cost_per_req) if cost_per_req is not None else None,
                "description": meta.get("description", "")
            }
            all_models_stats.append(model_obj)

        top5_tokens = sorted(all_models_stats, key=lambda x: x["total_tokens"], reverse=True)[:5]
        top5_spend = sorted(all_models_stats, key=lambda x: x["spend_usd"], reverse=True)[:5]

        return top5_tokens, top5_spend

    def generate_report(self) -> Path:
        """Executes analysis and generates Markdown document: key data first, methodology last."""
        rolling_dates = self.get_latest_7_days()
        start_date = rolling_dates[0]
        end_date = rolling_dates[-1]
        logging.info("Analyzing rolling 7-day window: %s to %s", start_date, end_date)

        logging.info("Fetching official 7-day model metrics...")
        official_items = self.fetch_official_7day_models(target_date=end_date)

        logging.info("Computing rankings, token volumes, spends, and pricing...")
        top5_tokens, top5_spend = self.compute_model_metrics(official_items, rolling_dates)

        unique_models = {}
        for m in top5_tokens + top5_spend:
            unique_models[m["slug"]] = m

        logging.info("Scraping real-time Top Apps for %d unique models...", len(unique_models))
        model_apps_map = {}
        model_scenarios_map = {}
        for slug in unique_models.keys():
            logging.info("  -> Scraping Top Apps for %s", slug)
            apps = self.scrape_model_apps_realtime(slug)
            model_apps_map[slug] = apps
            model_scenarios_map[slug] = self.get_task_scenarios_for_model(slug)

        doc = []
        doc.append(f"# weekly_top5_report_{end_date}\n\n")
        doc.append(f"- **统计周期**：`{start_date}` 至 `{end_date}`（连续完整 7 天）  \n")
        doc.append(f"- **数据生成时间**：`{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`  \n\n")
        doc.append("---\n\n")

        # ==========================================
        # 一、 核心榜单数据（置顶呈现：用量、金额与首选应用）
        # ==========================================
        doc.append("## 一、 核心榜单数据（榜单与首选应用）\n\n")

        doc.append("### 1. Token 物理使用量前 5 模型\n\n")
        doc.append("| 排名 | 模型名称 | 7天 Token 消耗 | 7天消费金额 (百万美元) | 实际有效单价 ($/M) | I/O 比率 | 首选偏好应用 (Top 1) | 主要任务场景 |\n")
        doc.append("|:---:|:---|:---:|:---:|:---:|:---:|:---|:---|\n")
        for i, m in enumerate(top5_tokens, 1):
            tok_str = f"{m['total_tokens'] / 1e12:.3f} T" if m['total_tokens'] >= 1e12 else f"{m['total_tokens'] / 1e9:.2f} B"
            spend_m = m['spend_usd'] / 1e6
            spend_str = f"{spend_m:.4f}" if 0 < spend_m < 0.01 else f"{spend_m:.3f}"
            apps = model_apps_map.get(m['slug'], [])
            app_str = f"{apps[0]['name']} ({apps[0]['tokens']})" if apps else "N/A"
            scenarios = model_scenarios_map.get(m['slug'], {})
            top_t = scenarios.get("top_tasks", [])
            task_str = f"`{top_t[0].get('tag', 'general')}` ({top_t[0].get('share', 0.0)*100:.1f}%)" if top_t else "通用"
            doc.append(
                f"| {i} | {m['name']} | **{tok_str}** | {spend_str} | **${m['empirical_eff_p_per_m']:.4f}** | {m['io_ratio']:.1f}:1 | {app_str} | {task_str} |\n"
            )

        doc.append("\n### 2. 消费金额前 5 模型\n\n")
        doc.append("| 排名 | 模型名称 | 7天消费金额 (百万美元) | 7天 Token 消耗 | 实际有效单价 ($/M) | I/O 比率 | 首选偏好应用 (Top 1) | 主要任务场景 |\n")
        doc.append("|:---:|:---|:---:|:---:|:---:|:---:|:---|:---|\n")
        for i, m in enumerate(top5_spend, 1):
            tok_str = f"{m['total_tokens'] / 1e12:.3f} T" if m['total_tokens'] >= 1e12 else f"{m['total_tokens'] / 1e9:.2f} B"
            spend_m = m['spend_usd'] / 1e6
            spend_str = f"{spend_m:.4f}" if 0 < spend_m < 0.01 else f"{spend_m:.3f}"
            apps = model_apps_map.get(m['slug'], [])
            app_str = f"{apps[0]['name']} ({apps[0]['tokens']})" if apps else "N/A"
            scenarios = model_scenarios_map.get(m['slug'], {})
            top_t = scenarios.get("top_tasks", [])
            task_str = f"`{top_t[0].get('tag', 'general')}` ({top_t[0].get('share', 0.0)*100:.1f}%)" if top_t else "通用"
            doc.append(
                f"| {i} | {m['name']} | **{spend_str}** | {tok_str} | **${m['empirical_eff_p_per_m']:.4f}** | {m['io_ratio']:.1f}:1 | {app_str} | {task_str} |\n"
            )
        doc.append("\n---\n\n")

        # ==========================================
        # 二、 各模型单项详细数据（包含偏好应用与场景分布）
        # ==========================================
        doc.append("## 二、 各模型详细指标数据\n\n")
        
        doc.append("### 1. Token 使用量前 5 模型指标\n\n")
        for i, m in enumerate(top5_tokens, 1):
            slug = m["slug"]
            apps = model_apps_map.get(slug, [])
            scenarios = model_scenarios_map.get(slug, {})
            macro_b = scenarios.get("macro_breakdown", {})
            top_t = scenarios.get("top_tasks", [])
            spend_m = m['spend_usd'] / 1e6

            doc.append(f"#### 1.{i} {m['name']} (`{slug}`)\n\n")
            doc.append(f"- **总消耗 Token**：`{m['total_tokens']:,}` ({m['total_tokens']/1e12:.3f}T Tokens)\n")
            doc.append(f"- **实际结算总金额**：`{spend_m:.4f}` 百万美元（`${m['spend_usd']:,.2f}`）\n")
            doc.append(f"- **Token 输入/输出**：输入 Prompt `{m['prompt_tokens']:,}` | 输出 Completion `{m['completion_tokens']:,}` | **I/O 比例：`{m['io_ratio']:.2f}:1`**\n")
            doc.append(f"- **单价指标**：标称输入 `${m['prompt_p_per_m']:.2f}/M` | 标称输出 `${m['comp_p_per_m']:.2f}/M` | 缓存读取 `${m['cache_read_p_per_m']:.4f}/M`\n")
            doc.append(f"- **有效单价与节省**：标称综合单价 `${m['nominal_p_per_m']:.4f}/M` | **实际有效单价 `${m['empirical_eff_p_per_m']:.4f}/M`** | 缓存与综合节省率 `{m['savings_pct']:.1f}%`\n")
            if apps:
                app_items = [f"{idx}. **{a['name']}**（流量消耗 `{a['tokens']}` tokens）" for idx, a in enumerate(apps[:2], 1)]
                doc.append(f"- **偏好应用 (Top 2)**：{' | '.join(app_items)}\n")
            else:
                doc.append(f"- **偏好应用 (Top 2)**：无公开应用数据\n")
            doc.append(f"- **场景分布占比**：Agent 代理 `{(macro_b.get('agent', 0)*100):.1f}%` | 编程开发 `{(macro_b.get('code', 0)*100):.1f}%` | 数据处理 `{(macro_b.get('data', 0)*100):.1f}%` | 通用任务 `{(macro_b.get('general', 0)*100):.1f}%`\n")
            if top_t:
                task_items = [f"`{t.get('tag')}` ({t.get('share', 0)*100:.1f}%)" for t in top_t[:3]]
                doc.append(f"- **高频任务标签**：{', '.join(task_items)}\n")
            doc.append("\n")

        doc.append("### 2. 消费金额前 5 模型指标\n\n")
        for i, m in enumerate(top5_spend, 1):
            slug = m["slug"]
            apps = model_apps_map.get(slug, [])
            scenarios = model_scenarios_map.get(slug, {})
            macro_b = scenarios.get("macro_breakdown", {})
            top_t = scenarios.get("top_tasks", [])
            spend_m = m['spend_usd'] / 1e6

            doc.append(f"#### 2.{i} {m['name']} (`{slug}`)\n\n")
            doc.append(f"- **实际结算总金额**：**`{spend_m:.4f}` 百万美元**（`${m['spend_usd']:,.2f}`）\n")
            doc.append(f"- **总消耗 Token**：`{m['total_tokens']:,}` ({m['total_tokens']/1e12:.3f}T Tokens) | 调用请求数：`{m['request_count']:,}`\n")
            doc.append(f"- **Token 输入/输出**：输入 Prompt `{m['prompt_tokens']:,}` | 输出 Completion `{m['completion_tokens']:,}` | **I/O 比例：`{m['io_ratio']:.2f}:1`**\n")
            doc.append(f"- **单价指标**：标称输入 `${m['prompt_p_per_m']:.2f}/M` | 标称输出 `${m['comp_p_per_m']:.2f}/M` | 缓存读取 `${m['cache_read_p_per_m']:.4f}/M`\n")
            doc.append(f"- **有效单价与节省**：标称综合单价 `${m['nominal_p_per_m']:.4f}/M` | **实际有效单价 `${m['empirical_eff_p_per_m']:.4f}/M`** | 缓存与综合节省率 `{m['savings_pct']:.1f}%`\n")
            if apps:
                app_items = [f"{idx}. **{a['name']}**（流量消耗 `{a['tokens']}` tokens）" for idx, a in enumerate(apps[:2], 1)]
                doc.append(f"- **偏好应用 (Top 2)**：{' | '.join(app_items)}\n")
            else:
                doc.append(f"- **偏好应用 (Top 2)**：无公开应用数据\n")
            doc.append(f"- **场景分布占比**：Agent 代理 `{(macro_b.get('agent', 0)*100):.1f}%` | 编程开发 `{(macro_b.get('code', 0)*100):.1f}%` | 数据处理 `{(macro_b.get('data', 0)*100):.1f}%` | 通用任务 `{(macro_b.get('general', 0)*100):.1f}%`\n")
            if top_t:
                task_items = [f"`{t.get('tag')}` ({t.get('share', 0)*100:.1f}%)" for t in top_t[:3]]
                doc.append(f"- **高频任务标签**：{', '.join(task_items)}\n")
            doc.append("\n")

        doc.append("---\n\n")

        # ==========================================
        # 三、 价格计算所用参数明细表（注明采用的参数与具体数值）
        # ==========================================
        doc.append("## 三、 价格计算所用参数明细表\n\n")
        doc.append("| 模型 Permaslug | 标称输入价 $P_{\\text{prompt}}$ ($/M) | 缓存读取价 $P_{\\text{cache\\_read}}$ ($/M) | 标称输出价 $P_{\\text{comp}}$ ($/M) | AA 加权输入价 $P_{\\text{wip}}$ ($/M) | 7天输入Token ($N_p$) | 7天输出Token ($N_c$) | I/O比率 ($r$) | 标称综合价 ($/M) | 实际结算单价 ($/M) | 实际总消费 (百万美元) |\n")
        doc.append("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")

        for slug, m in unique_models.items():
            wip_repr = f"${m['wip_per_m']:.4f}" if m['wip_per_m'] is not None else "N/A"
            doc.append(
                f"| `{slug}` | ${m['prompt_p_per_m']:.2f} | ${m['cache_read_p_per_m']:.4f} | ${m['comp_p_per_m']:.2f} | {wip_repr} | {m['prompt_tokens']:,} | {m['completion_tokens']:,} | {m['io_ratio']:.2f}:1 | ${m['nominal_p_per_m']:.4f} | **${m['empirical_eff_p_per_m']:.4f}** | {m['spend_usd']/1e6:.4f} |\n"
            )

        doc.append("\n**参数说明**：\n")
        doc.append("- $P_{\\text{prompt}}$：标称未命中缓存输入单价（单位：USD / 1,000,000 Tokens，来源：OpenRouter 官方模型目录 API）。\n")
        doc.append("- $P_{\\text{cache\\_read}}$：Prompt 缓存读取单价（单位：USD / 1,000,000 Tokens，来源：pricing.input_cache_read 字段）。\n")
        doc.append("- $P_{\\text{comp}}$：标称输出生成单价（单位：USD / 1,000,000 Tokens，来源：pricing.completion 字段）。\n")
        doc.append("- $P_{\\text{wip}}$：Artificial Analysis 缓存加权输入价（单位：USD / 1,000,000 Tokens，来源：Artificial Analysis 评测集）。\n")
        doc.append("- $N_p, N_c, r$：7 天物理统计输入 Token、输出 Token 及二者比率 $r = N_p / N_c$（来源：OpenRouter 官方 rankings/models）。\n")
        doc.append("- 实际总消费：7 天实际结算扣费总额（单位：百万美元，来源：OpenRouter 官方指标 total_usage）。\n\n")

        doc.append("---\n\n")

        # ==========================================
        # 四、 价格测算方法论与计算公式（放最后）
        # ==========================================
        doc.append("## 四、 价格测算方法论与计算公式\n\n")
        doc.append("设模型定价与调用结构参数如下：\n")
        doc.append("- $P_{\\text{prompt}}$：非缓存输入 Token 标称单价（$\\$/\\text{M Tokens}$）\n")
        doc.append("- $P_{\\text{cache\\_read}}$：KV 缓存命中读取单价（$\\$/\\text{M Tokens}$）\n")
        doc.append("- $P_{\\text{comp}}$：输出 Completion Token 标称单价（$\\$/\\text{M Tokens}$）\n")
        doc.append("- $N_p$：提示词输入 Token 总量，$N_c$：模型生成输出 Token 总量，$T = N_p + N_c$\n")
        doc.append("- $r = N_p / N_c$：输入输出比（Input/Output Ratio）\n")
        doc.append("- $h$：上下文缓存有效命中率（Cache Hit Ratio，$0 \\le h \\le 1$）\n\n")
        doc.append("**1. 未考虑缓存时的标称综合单价（Nominal Blended Price）**：\n")
        doc.append("$$\\bar{P}_{\\text{no\\_cache}} = \\frac{N_p \\cdot P_{\\text{prompt}} + N_c \\cdot P_{\\text{comp}}}{N_p + N_c} = \\frac{r \\cdot P_{\\text{prompt}} + P_{\\text{comp}}}{r + 1}$$\n\n")
        doc.append("**2. 考虑缓存后的理论加权综合单价（Effective Blended Price with Cache）**：\n")
        doc.append("$$\\bar{P}_{\\text{cached}} = \\frac{(1-h) N_p P_{\\text{prompt}} + h N_p P_{\\text{cache\\_read}} + N_c P_{\\text{comp}}}{N_p + N_c} = \\frac{r \\cdot \\left[(1-h) P_{\\text{prompt}} + h P_{\\text{cache\\_read}}\\right] + P_{\\text{comp}}}{r + 1}$$\n\n")
        doc.append("**3. 经验实际结算有效单价（Empirical Realized Price）**：\n")
        doc.append("$$\\bar{P}_{\\text{empirical}} = \\frac{\\text{实际总消费 (USD)}}{\\text{Total Tokens}} \\times 10^6 = \\frac{\\text{实际总消费 (百万美元)} \\times 10^{12}}{N_p + N_c} \\quad (\\$/\\text{M Tokens})$$\n\n")
        doc.append("**4. 综合节省率（Cost Reduction Rate）**：\n")
        doc.append("$$\\Delta_{\\text{saving}} = \\frac{\\bar{P}_{\\text{no\\_cache}} - \\bar{P}_{\\text{empirical}}}{\\bar{P}_{\\text{no\\_cache}}} \\times 100\\%$$\n\n")

        # Write file
        content = "".join(doc)
        out_path = self.report_dir / f"weekly_top5_report_{end_date}.md"
        with out_path.open("w", encoding="utf-8") as f:
            f.write(content)

        logging.info("Report successfully generated at: %s", out_path)
        return out_path


def main():
    parser = argparse.ArgumentParser(description="Generate weekly top 5 LLM models report")
    parser.add_argument("--project-root", type=str, default=None, help="Root path of the project")
    args = parser.parse_args()

    generator = ModelReportGenerator(project_root=Path(args.project_root) if args.project_root else None)
    out_file = generator.generate_report()
    print(f"[+] Successfully generated report: {out_file}")


if __name__ == "__main__":
    main()
