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
from collections import defaultdict
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

    def _find_snapshot_file(self, subdir: str, target_date: Optional[str] = None) -> Optional[Path]:
        """Finds the most appropriate snapshot JSON file in a given directory."""
        sdir = self.data_dir / subdir
        if not sdir.exists():
            return None
        files = sorted([
            f for f in sdir.glob("*.json")
            if re.match(r"^\d{4}-\d{2}-\d{2}$", f.stem)
        ], key=lambda x: x.stem)
        if not files:
            return None
        if target_date:
            candidates = [f for f in files if f.stem <= target_date]
            if candidates:
                return candidates[-1]
        return files[-1]

    def _load_local_datasets(self, target_date: Optional[str] = None) -> None:
        """Loads models metadata, benchmarks, and task spend snapshots dynamically."""
        self.models_meta = []
        self.meta_by_canon = {}
        self.meta_by_id = {}
        self.benchmarks = {}
        self.task_spend = {}

        # 1. Models metadata
        models_file = self._find_snapshot_file("models", target_date)
        if models_file and models_file.exists():
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
        bench_file = self._find_snapshot_file("benchmarks", target_date)
        if bench_file and bench_file.exists():
            with bench_file.open("r", encoding="utf-8") as f:
                self.benchmarks = json.load(f).get("data", {})

        # 3. Task spend (macro category & tasks distribution)
        ts_file = self._find_snapshot_file("task_spend", target_date)
        if ts_file and ts_file.exists():
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
        Prefers local cached snapshot in data/openrouter/rankings_models.
        Note: The 7-day rolling window ending on target_date is recorded in the snapshot
        crawled on (target_date + 1 day) or in a snapshot containing target_date records.
        """
        if target_date:
            candidates = []
            try:
                target_dt = datetime.datetime.strptime(target_date, "%Y-%m-%d").date()
                next_day_str = (target_dt + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                candidates.append(self.data_dir / "rankings_models" / f"{next_day_str}.json")
            except Exception:
                pass
            candidates.append(self.data_dir / "rankings_models" / f"{target_date}.json")

            for local_snap in candidates:
                if local_snap.exists():
                    try:
                        with local_snap.open("r", encoding="utf-8") as f:
                            d = json.load(f)
                            data = d.get("data", [])
                            # Check whether this snapshot contains target_date records
                            if any(r.get("date") == f"{target_date} 00:00:00" for r in data):
                                logging.info("Loaded official rankings/models from local snapshot: %s", local_snap)
                                return data
                    except Exception as e:
                        logging.warning("Failed to read local snapshot %s: %s", local_snap, e)

            # Fallback to candidate file existence if date matching didn't trigger
            for local_snap in candidates:
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

    def fetch_official_7day_models_spend(self, target_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetches the official OpenRouter rolling 7-day model spend rankings endpoint (metric=spend).
        Prefers local cached snapshot in data/openrouter/rankings_models_spend.
        """
        if target_date:
            candidates = []
            try:
                target_dt = datetime.datetime.strptime(target_date, "%Y-%m-%d").date()
                next_day_str = (target_dt + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                candidates.append(self.data_dir / "rankings_models_spend" / f"{next_day_str}.json")
            except Exception:
                pass
            candidates.append(self.data_dir / "rankings_models_spend" / f"{target_date}.json")

            for local_snap in candidates:
                if local_snap.exists():
                    try:
                        with local_snap.open("r", encoding="utf-8") as f:
                            d = json.load(f)
                            data = d.get("data", [])
                            if any(r.get("date") == f"{target_date} 00:00:00" for r in data):
                                logging.info("Loaded official rankings/models?metric=spend from local snapshot: %s", local_snap)
                                return data
                    except Exception as e:
                        logging.warning("Failed to read local snapshot %s: %s", local_snap, e)

            for local_snap in candidates:
                if local_snap.exists():
                    try:
                        with local_snap.open("r", encoding="utf-8") as f:
                            d = json.load(f)
                            data = d.get("data", [])
                            if data:
                                logging.info("Loaded official rankings/models?metric=spend from local snapshot: %s", local_snap)
                                return data
                    except Exception as e:
                        logging.warning("Failed to read local snapshot %s: %s", local_snap, e)

        url = "https://openrouter.ai/api/frontend/v1/rankings/models?metric=spend"
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if target_date and data:
                    out_dir = self.data_dir / "rankings_models_spend"
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
                        logging.info("Cached rankings_models_spend snapshot to %s", out_file)
                    except Exception as w_err:
                        logging.warning("Failed to save local rankings_models_spend snapshot: %s", w_err)
                return data
            else:
                logging.warning("Official rankings/models?metric=spend HTTP %s", resp.status_code)
        except Exception as e:
            logging.warning("Failed to fetch official rankings/models?metric=spend: %s", e)
        return []

    @staticmethod
    def _parse_token_unit(s: str) -> float:
        s = s.strip()
        if not s:
            return 0.0
        if s.endswith("T"):
            return float(s[:-1]) * 1e12
        if s.endswith("B"):
            return float(s[:-1]) * 1e9
        if s.endswith("M"):
            return float(s[:-1]) * 1e6
        if s.endswith("K"):
            return float(s[:-1]) * 1e3
        return float(s)

    def scrape_model_apps_realtime(self, slug: str) -> List[Dict[str, Any]]:
        """
        Scrapes real-time Top Apps from OpenRouter model page.
        Does not persist to disk, returning directly as requested.
        Calculates relative traffic share percentage for each app.
        """
        clean_slug = re.sub(r"-\d{8}$", "", slug)
        candidates = [clean_slug, slug]
        if clean_slug == slug:
            candidates = [slug]

        for s in candidates:
            url = f"https://openrouter.ai/models/{s}"
            try:
                resp = self.session.get(url, timeout=10)
                if resp.status_code != 200:
                    continue
                text = resp.text

                # Strategy 1: Parse from Next.js RSC dehydrated state for highest precision
                idx = text.find("top_apps")
                if idx != -1:
                    p_start = text.rfind("self.__next_f.push", 0, idx)
                    p_end = text.find("</script>", idx)
                    if p_start != -1 and p_end != -1:
                        chunk = text[p_start:p_end]
                        m = re.match(r"self\.__next_f\.push\(\[(\d+),\s*\"(.*)\"\]\)", chunk, re.DOTALL)
                        if m:
                            unescaped = m.group(2).encode("utf-8").decode("unicode_escape")
                            apps_idx = unescaped.find('"top_apps":[')
                            if apps_idx != -1:
                                bracket_start = unescaped.find("[", apps_idx)
                                depth = 0
                                bracket_end = -1
                                for i in range(bracket_start, len(unescaped)):
                                    if unescaped[i] == "[":
                                        depth += 1
                                    elif unescaped[i] == "]":
                                        depth -= 1
                                        if depth == 0:
                                            bracket_end = i + 1
                                            break
                                if bracket_end != -1:
                                    try:
                                        apps_raw = json.loads(unescaped[bracket_start:bracket_end])
                                        tot_tok = sum(float(a.get("total_tokens", 0)) for a in apps_raw)
                                        results = []
                                        for a in apps_raw:
                                            tok = float(a.get("total_tokens", 0))
                                            pct = (tok / tot_tok * 100.0) if tot_tok > 0 else 0.0
                                            title = a.get("app", {}).get("title") or "Unknown"
                                            desc = a.get("app", {}).get("description") or ""
                                            if tok >= 1e12:
                                                tok_str = f"{tok/1e12:.2f}T"
                                            elif tok >= 1e9:
                                                tok_str = f"{tok/1e9:.1f}B"
                                            elif tok >= 1e6:
                                                tok_str = f"{tok/1e6:.1f}M"
                                            else:
                                                tok_str = f"{tok:,.0f}"
                                            results.append({
                                                "rank": int(a.get("rank", 0)),
                                                "name": title,
                                                "description": desc,
                                                "tokens": tok_str,
                                                "raw_tokens": tok,
                                                "share_pct": pct
                                            })
                                        if results:
                                            return results
                                    except Exception as e:
                                        logging.debug("RSC JSON parsing exception for %s: %s", url, e)

                # Strategy 2: HTML grid regex fallback
                row_pattern = re.compile(
                    r'<div class="grid w-full grid-cols-12 items-center">(.*?)</div>\s*</div>\s*</div>',
                    re.DOTALL
                )
                rows = row_pattern.findall(text)
                if rows:
                    results = []
                    for row in rows:
                        r_m = re.search(r"(\d+)<!-- -->\.", row)
                        name_m = re.search(r"<a [^>]*>(.*?)<svg", row)
                        tok_m = re.search(r"<span>([0-9\.]+[KMBT]?)</span>\s*<span[^>]*>tokens</span>", row)
                        if r_m and name_m and tok_m:
                            rank = int(r_m.group(1))
                            clean_name = re.sub(r"<[^>]+>", "", name_m.group(1)).strip()
                            tokens_str = tok_m.group(1)
                            num_tok = self._parse_token_unit(tokens_str)
                            results.append({
                                "rank": rank,
                                "name": clean_name,
                                "description": "",
                                "tokens": tokens_str,
                                "raw_tokens": num_tok
                            })
                    if results:
                        tot = sum(r["raw_tokens"] for r in results)
                        for r in results:
                            r["share_pct"] = (r["raw_tokens"] / tot * 100.0) if tot > 0 else 0.0
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
        """Extracts dominant macro category and top subtask tag for a model from task_spend snapshot."""
        clean = slug.split(":")[0]
        base_clean = re.sub(r"-\d{8}$", "", clean)
        candidates = {slug, clean, base_clean}

        spend_data = self.task_spend.get("spend", {})
        tasks = spend_data.get("tasks", [])
        matched_tasks = []

        macro_name_map = {
            "code": "编程开发",
            "agent": "Agent 代理",
            "data": "数据处理",
            "general": "通用任务"
        }

        for t in tasks:
            macro = t.get("macroCategory", "general")
            tag = t.get("tag", "general")
            for m_item in t.get("models", []):
                m_name = m_item.get("model", "")
                if any(c in m_name for c in candidates):
                    share = m_item.get("share", 0.0)
                    matched_tasks.append({
                        "tag": tag,
                        "macro": macro,
                        "macro_label": macro_name_map.get(macro, macro),
                        "share": share
                    })

        matched_tasks = sorted(matched_tasks, key=lambda x: x["share"], reverse=True)
        top_task = matched_tasks[0] if matched_tasks else None
        top_macro = top_task["macro_label"] if top_task else ""
        top_tag = top_task["tag"] if top_task else ""

        return {
            "top_macro": top_macro,
            "top_tag": top_tag
        }

    def generate_task_scenarios_section(self) -> List[str]:
        """Generates markdown section detailing full task scenarios, macro categories, and top models."""
        spend_data = self.task_spend.get("spend", {})
        macro_categories = spend_data.get("macroCategories", [])
        tasks = spend_data.get("tasks", [])

        if not macro_categories or not tasks:
            return []

        doc = []
        doc.append("## 三、 全平台任务场景大类与小类分布全景\n\n")
        window_days = spend_data.get("windowDays", 30)
        doc.append(
            f"> [!NOTE]\n"
            f"> **数据统计时间窗口说明**：全平台任务场景大类与小类分布数据来源于 OpenRouter 官方细分任务开销接口（`task-spend`）。"
            f"根据接口元数据定义，其统计窗口为**过去 {window_days} 天滚动消费支出（Rolling {window_days}-Day Window，`windowDays: {window_days}`）**，"
            f"以全平台各场景所消耗的美元金额为权重统计。该统计平滑了短期偶然波动，真实反映各模型在垂直生产场景与工作流中的中长期落地渗透情况（与周度榜单的 7 天滚动用量形成互补）。\n\n"
        )

        # 1. 宏观大类分布概览
        doc.append("### 1. 宏观大类分布概览\n\n")
        doc.append("| 宏观大类 | 标识 Key | 全平台支出占比 | 细分小类数量 | 核心特征 |\n")
        doc.append("|:---|:---:|:---:|:---:|:---|\n")

        macro_meta_info = {
            "general": ("General 通用与认知", "分类打标、长文写作、知识问答、数学推演等"),
            "agent": ("Agent 智能体代理", "复杂工作流自驱动、多步规划、工具调度分发等"),
            "code": ("Code 软件工程开发", "代码实现、调试排错、仓库扫描、终端执行等"),
            "data": ("Data 数据处理加工", "非结构化数据抽取、格式清洗与转换")
        }

        from collections import defaultdict
        tasks_by_macro = defaultdict(list)
        for t in tasks:
            tasks_by_macro[t.get("macroCategory", "general")].append(t)

        sorted_macros = sorted(macro_categories, key=lambda x: x.get("spendShare", 0.0), reverse=True)
        for m in sorted_macros:
            k = m.get("key", "")
            share = m.get("spendShare", 0.0) * 100
            sub_count = len(tasks_by_macro.get(k, []))
            name, feat = macro_meta_info.get(k, (m.get("label", k), "相关业务场景"))
            doc.append(f"| **{name}** | `{k}` | **{share:.2f}%** | {sub_count} 个 | {feat} |\n")

        doc.append("\n### 2. 全量大类与小类明细表\n\n")

        task_desc_map = {
            # Agent
            "agent:workflow_execution": "复杂自动化工作流编排与执行",
            "agent:multi_step_planning": "多步推理、目标规划与决策分解",
            "agent:tool_dispatch": "外部 Tool/Function 调度与参数组装",
            "agent:web_search": "联网检索与外部信息整合",
            "agent:memory_extraction": "会话长期记忆与状态提炼",
            # Code
            "code:general_impl": "通用业务逻辑与功能代码实现",
            "code:debugging": "代码缺陷排查与单元测试修复",
            "code:file_read_write": "单文件/跨文件读写与精准修改",
            "code:review_security": "代码评审与安全漏洞静态审查",
            "code:shell_execution": "Shell/Bash 终端指令与脚本执行",
            "code:frontend_ui": "前端界面、样式与组件开发",
            "code:repo_scan": "代码仓库全局扫描与上下文构建",
            "code:devops_config": "Dockerfile/CI-CD/K8s 配置文件编写",
            "code:sql_database": "数据库 SQL 编写与 Schema 设计",
            # Data
            "data:extraction": "非结构化文本/文档关键信息抽取",
            "data:transformation": "数据清洗、格式转换与 Schema 映射",
            # General
            "classification_tagging": "文本分类、意图识别与内容打标",
            "content_writing": "专业文章、长篇文案与创意写作",
            "roleplay_fiction": "虚拟角色扮演与小说剧情虚构",
            "qa_knowledge": "事实知识库问答与精准问答",
            "conversational_reply": "开放域多轮自然对话交互",
            "research_report": "行业深度研究报告与综合研报撰写",
            "customer_support": "智能客户服务与工单处理支持",
            "summarization": "长文档、会议纪要与摘要总结",
            "math": "复杂数学推演与公式计算求解",
            "security_audit": "安全合规审计与系统安全检测",
            "finance_trading": "金融财报分析与量化交易策略",
            "translation": "专业多语言翻译与本地化",
            "devops": "通用运维诊断与环境故障咨询",
        }

        macro_detail_headers = {
            "agent": "Agent 智能体类",
            "code": "Code 软件工程类",
            "data": "Data 数据处理类",
            "general": "General 通用与专业认知类"
        }

        def clean_model_name(raw_slug: str) -> str:
            clean = raw_slug.split(":")[0]
            base = re.sub(r"-\d{8}$", "", clean)
            meta = self.get_model_metadata(raw_slug) or self.get_model_metadata(clean) or self.get_model_metadata(base)
            name = meta.get("name") if meta else None
            if not name:
                name = clean.split("/")[-1]
            name = re.sub(r"^[^:]+:\s*", "", name)
            name = re.sub(r"\s*\((batch|free)\)", "", name, flags=re.I).strip()
            return name

        # Presentation order: descending order by spendShare
        sorted_macros = sorted(macro_categories, key=lambda x: x.get("spendShare", 0.0), reverse=True)

        for idx, m_info in enumerate(sorted_macros, 1):
            k = m_info.get("key", "")
            m_share = m_info.get("spendShare", 0.0) * 100
            m_header = macro_detail_headers.get(k, m_info.get("label", k))
            doc.append(f"#### 2.{idx} {m_header}（全平台支出：{m_share:.2f}%）\n\n")
            doc.append("| 细分小类标签 (`tag`) | 中文业务场景 | 全平台支出占比 | 场景领跑模型（市场份额） |\n")
            doc.append("|:---|:---|:---:|:---|\n")

            sub_tasks = tasks_by_macro.get(k, [])
            sub_tasks = sorted(sub_tasks, key=lambda x: x.get("spendShareOfTotal", 0.0), reverse=True)
            for st in sub_tasks:
                tag = st.get("tag", "")
                desc = task_desc_map.get(tag, "细分专业场景")
                t_share = st.get("spendShareOfTotal", 0.0) * 100
                models = st.get("models", [])
                top_m = models[0] if models else None
                if top_m:
                    m_title = clean_model_name(top_m.get("model", ""))
                    m_pct = top_m.get("share", 0.0) * 100
                    if tag == "code:repo_scan":
                        top_repr = f"**{m_title} ({m_pct:.1f}%)**"
                    else:
                        top_repr = f"{m_title} ({m_pct:.1f}%)"
                else:
                    top_repr = "无公开模型"
                doc.append(f"| `{tag}` | {desc} | {t_share:.2f}% | {top_repr} |\n")
            doc.append("\n")

        doc.append("---\n\n")
        return doc


    def compute_model_metrics(
        self,
        official_items: List[Dict[str, Any]],
        rolling_dates: List[str],
        spend_items: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Computes detailed token, spend, pricing, and cache metrics for all models using Path 1.
        Properly accumulates across variants for each model_permaslug.
        Returns (top5_by_tokens, top5_by_spend).
        """
        start_date = rolling_dates[0]
        end_date = rolling_dates[-1]

        if spend_items is None:
            spend_items = self.fetch_official_7day_models_spend(target_date=end_date)

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
            # Filter out stale historical rows if row has a date field older than start_date
            row_date = row.get("date", "")
            if row_date and row_date < f"{start_date} 00:00:00":
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

        spend_share_by_slug: Dict[str, float] = {}
        if spend_items:
            for row in spend_items:
                s = row.get("model_permaslug")
                if not s:
                    continue
                row_date = row.get("date", "")
                if row_date and row_date < f"{start_date} 00:00:00":
                    continue
                val = float(row.get("rankingMetricValue") or 0.0)
                spend_share_by_slug[s] = spend_share_by_slug.get(s, 0.0) + val

        all_slugs = set(daily_tokens.keys()).union(off_by_slug.keys()).union(spend_share_by_slug.keys())
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

            # Consistently derive total tokens:
            if official_tot > 0:
                tot_tokens = official_tot
            else:
                tot_tokens = daily_tot
                p_tok = int(tot_tokens * 0.90)
                c_tok = tot_tokens - p_tok

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

            prompt_p_per_m = prompt_p * 1e6
            cache_read_p_per_m = cache_read_p * 1e6
            comp_p_per_m = comp_p * 1e6

            # Platform spend share percentage
            spend_share_pct = spend_share_by_slug.get(slug, 0.0) * 100.0

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
                "spend_share_pct": spend_share_pct,
                "request_count": req_count,
                "io_ratio": io_ratio,
                "prompt_p_per_m": prompt_p_per_m,
                "comp_p_per_m": comp_p_per_m,
                "cache_read_p_per_m": cache_read_p_per_m,
                "cache_write_p_per_m": cache_write_p * 1e6,
                "cost_per_req": float(cost_per_req) if cost_per_req is not None else None,
                "description": meta.get("description", "")
            }
            all_models_stats.append(model_obj)

        # Filter valid LLMs for ranking (exclude non-text models like pure audio/video)
        valid_llms = [
            m for m in all_models_stats
            if m["total_tokens"] > 0
            and not any(k in m["slug"].lower() for k in ["kling-video", "whisper", "embedding", "transcribe"])
        ]

        top5_tokens = sorted(all_models_stats, key=lambda x: x["total_tokens"], reverse=True)[:5]

        has_spend_share = any(m["spend_share_pct"] > 0 for m in valid_llms)
        has_historical_spend = any(m["spend_usd"] > 0 for m in valid_llms)

        if has_spend_share:
            top5_spend = sorted(valid_llms, key=lambda x: x["spend_share_pct"], reverse=True)[:5]
        elif has_historical_spend:
            top5_spend = sorted(valid_llms, key=lambda x: x["spend_usd"], reverse=True)[:5]
        else:
            top5_spend = sorted(valid_llms, key=lambda x: x["total_tokens"], reverse=True)[:5]

        return top5_tokens, top5_spend

    def compute_vendor_metrics(
        self,
        spend_items: List[Dict[str, Any]],
        official_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Aggregates rolling 7-day spend shares and token consumption by model vendor/creator."""
        tokens_by_slug = defaultdict(int)
        for row in official_items:
            slug = row.get("model_permaslug", "")
            p = int(row.get("total_prompt_tokens", 0))
            c = int(row.get("total_completion_tokens", 0))
            tokens_by_slug[slug] += (p + c)

        def normalize_vendor(prefix: str) -> str:
            p = prefix.lower()
            if p in ("meta-llama", "meta"):
                return "Meta"
            elif p in ("anthropic",):
                return "Anthropic"
            elif p in ("openai",):
                return "OpenAI"
            elif p in ("google",):
                return "Google"
            elif p in ("deepseek",):
                return "DeepSeek (深度求索)"
            elif p in ("z-ai",):
                return "智谱 AI (Z.ai)"
            elif p in ("moonshotai",):
                return "月之暗面 (Moonshot AI)"
            elif p in ("x-ai",):
                return "xAI"
            elif p in ("qwen",):
                return "阿里通义 (Qwen)"
            elif p in ("stepfun",):
                return "阶跃星辰 (StepFun)"
            elif p in ("xiaomi",):
                return "小米 (Xiaomi)"
            elif p in ("tencent",):
                return "腾讯混元 (Tencent)"
            elif p in ("minimax",):
                return "MiniMax"
            elif p in ("mistralai",):
                return "Mistral AI"
            return prefix.title()

        # First aggregate spend share across variants (standard, batch, etc.)
        spend_share_by_slug = defaultdict(float)
        for row in spend_items:
            slug = row.get("model_permaslug", "")
            val = float(row.get("rankingMetricValue") or 0.0)
            if slug:
                spend_share_by_slug[slug] += val

        vendor_spend = defaultdict(float)
        vendor_tokens = defaultdict(int)
        vendor_models = defaultdict(list)

        all_slugs = set(tokens_by_slug.keys()).union(spend_share_by_slug.keys())
        for slug in all_slugs:
            prefix = slug.split("/")[0] if "/" in slug else "other"
            vname = normalize_vendor(prefix)
            share_val = spend_share_by_slug.get(slug, 0.0)
            t_tok = tokens_by_slug.get(slug, 0)

            vendor_spend[vname] += share_val
            vendor_tokens[vname] += t_tok

            meta = self.get_model_metadata(slug)
            raw_name = meta.get("name") if meta else slug.split("/")[-1]
            mname = re.sub(r"^[^:]+:\s*", "", raw_name)
            vendor_models[vname].append({
                "slug": slug,
                "name": mname,
                "share_pct": share_val * 100.0,
                "tokens": t_tok
            })

        results = []
        for vname, spend_share in sorted(vendor_spend.items(), key=lambda x: x[1], reverse=True):
            v_models = sorted(vendor_models[vname], key=lambda x: x["share_pct"], reverse=True)
            results.append({
                "vendor": vname,
                "spend_share_pct": spend_share * 100.0,
                "total_tokens": vendor_tokens[vname],
                "top_model": v_models[0] if v_models else None,
                "models": v_models
            })
        return results

    def generate_report(self, target_end_date: Optional[str] = None) -> Path:
        """Executes analysis and generates Markdown document: key data first, methodology last."""
        if target_end_date:
            end_date = target_end_date
            latest_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            rolling_dates = [(latest_dt - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
        else:
            rolling_dates = self.get_latest_7_days()
            end_date = rolling_dates[-1]

        start_date = rolling_dates[0]
        logging.info("Analyzing rolling 7-day window: %s to %s", start_date, end_date)

        # Reload metadata dynamically aligned with end_date / report generation date
        try:
            report_snap_dt = (datetime.datetime.strptime(end_date, "%Y-%m-%d").date() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        except Exception:
            report_snap_dt = end_date
        self._load_local_datasets(target_date=report_snap_dt)

        logging.info("Fetching official 7-day model metrics (tokens)...")
        official_items = self.fetch_official_7day_models(target_date=end_date)

        logging.info("Fetching official 7-day model metrics (spend)...")
        spend_items = self.fetch_official_7day_models_spend(target_date=end_date)

        logging.info("Computing rankings, token volumes, spends, and pricing...")
        top5_tokens, top5_spend = self.compute_model_metrics(official_items, rolling_dates, spend_items=spend_items)
        top5_vendors = self.compute_vendor_metrics(spend_items, official_items)[:5]

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
        doc.append("| 排名 | 模型名称 | 7天 Token 消耗 | 全平台消费份额占比 | I/O 比率 | 标称输入单价 ($/M) | 标称输出单价 ($/M) | 首选偏好应用 (Top 1 份额) |\n")
        doc.append("|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---|\n")
        for i, m in enumerate(top5_tokens, 1):
            tok_str = f"{m['total_tokens'] / 1e12:.3f} T" if m['total_tokens'] >= 1e12 else f"{m['total_tokens'] / 1e9:.2f} B"
            share_str = f"{m['spend_share_pct']:.2f}%" if m['spend_share_pct'] > 0 else "N/A"
            apps = model_apps_map.get(m['slug'], [])
            app_str = f"{apps[0]['name']} ({apps[0].get('share_pct', 0.0):.1f}%)" if apps else "N/A"
            doc.append(
                f"| {i} | {m['name']} | **{tok_str}** | **{share_str}** | {m['io_ratio']:.1f}:1 | ${m['prompt_p_per_m']:.4f} | ${m['comp_p_per_m']:.4f} | {app_str} |\n"
            )

        doc.append("\n### 2. 全平台消费份额前 5 模型\n\n")
        doc.append("| 排名 | 模型名称 | 全平台消费份额占比 | 7天 Token 消耗 | I/O 比率 | 标称输入单价 ($/M) | 标称输出单价 ($/M) | 首选偏好应用 (Top 1 份额) |\n")
        doc.append("|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---|\n")
        for i, m in enumerate(top5_spend, 1):
            tok_str = f"{m['total_tokens'] / 1e12:.3f} T" if m['total_tokens'] >= 1e12 else f"{m['total_tokens'] / 1e9:.2f} B"
            share_str = f"{m['spend_share_pct']:.2f}%" if m['spend_share_pct'] > 0 else "N/A"
            apps = model_apps_map.get(m['slug'], [])
            app_str = f"{apps[0]['name']} ({apps[0].get('share_pct', 0.0):.1f}%)" if apps else "N/A"
            doc.append(
                f"| {i} | {m['name']} | **{share_str}** | {tok_str} | {m['io_ratio']:.1f}:1 | ${m['prompt_p_per_m']:.4f} | ${m['comp_p_per_m']:.4f} | {app_str} |\n"
            )

        doc.append("\n### 3. 全平台消费份额前 5 厂商\n\n")
        doc.append("| 排名 | 厂商名称 | 7天全平台消费份额占比 | 7天 Token 消耗总量 | 主力拉动模型 (单模型消费份额) |\n")
        doc.append("|:---:|:---|:---:|:---:|:---|\n")
        for i, v in enumerate(top5_vendors, 1):
            v_tok = v["total_tokens"]
            v_tok_str = f"{v_tok / 1e12:.3f} T" if v_tok >= 1e12 else f"{v_tok / 1e9:.2f} B"
            top_m = v["top_model"]
            m_label = f"{top_m['name']} ({top_m['share_pct']:.2f}%)" if top_m else "N/A"
            doc.append(
                f"| {i} | {v['vendor']} | **{v['spend_share_pct']:.2f}%** | {v_tok_str} | {m_label} |\n"
            )
        doc.append("\n---\n\n")

        # ==========================================
        # 二、 各模型详细指标数据
        # ==========================================
        doc.append("## 二、 各模型详细指标数据\n\n")
        
        doc.append("### 1. Token 使用量前 5 模型指标\n\n")
        for i, m in enumerate(top5_tokens, 1):
            slug = m["slug"]
            apps = model_apps_map.get(slug, [])
            scenarios = model_scenarios_map.get(slug, {})

            doc.append(f"#### 1.{i} {m['name']} (`{slug}`)\n\n")
            doc.append(f"- **总消耗 Token**：`{m['total_tokens']:,}` ({m['total_tokens']/1e12:.3f}T Tokens)\n")
            if m['spend_share_pct'] > 0:
                doc.append(f"- **全平台消费份额占比**：`{m['spend_share_pct']:.2f}%`\n")
            doc.append(f"- **Token 输入/输出**：输入 Prompt `{m['prompt_tokens']:,}` | 输出 Completion `{m['completion_tokens']:,}` | **I/O 比例：`{m['io_ratio']:.2f}:1`**\n")
            doc.append(f"- **官方标称单价**：标称输入 `${m['prompt_p_per_m']:.4f}/M` | 标称输出 `${m['comp_p_per_m']:.4f}/M` | 缓存读取 `${m['cache_read_p_per_m']:.4f}/M`\n")
            if apps:
                app_items = [
                    f"{idx}. **{a['name']}**（流量份额 `{a.get('share_pct', 0.0):.1f}%`，累计 `{a['tokens']}` tokens）"
                    for idx, a in enumerate(apps[:2], 1)
                ]
                doc.append(f"- **偏好应用 (Top 2)**：{' | '.join(app_items)}\n")
            else:
                doc.append(f"- **偏好应用 (Top 2)**：无公开应用数据\n")
            top_tag = scenarios.get("top_tag")
            if top_tag:
                doc.append(f"- **优势细分场景**：`{top_tag}`\n")
            doc.append("\n")

        doc.append("### 2. 全平台消费份额前 5 模型指标\n\n")
        for i, m in enumerate(top5_spend, 1):
            slug = m["slug"]
            apps = model_apps_map.get(slug, [])
            scenarios = model_scenarios_map.get(slug, {})

            doc.append(f"#### 2.{i} {m['name']} (`{slug}`)\n\n")
            if m['spend_share_pct'] > 0:
                doc.append(f"- **全平台消费份额占比**：**`{m['spend_share_pct']:.2f}%`**\n")
            doc.append(f"- **总消耗 Token**：`{m['total_tokens']:,}` ({m['total_tokens']/1e12:.3f}T Tokens) | 调用请求数：`{m['request_count']:,}`\n")
            doc.append(f"- **Token 输入/输出**：输入 Prompt `{m['prompt_tokens']:,}` | 输出 Completion `{m['completion_tokens']:,}` | **I/O 比例：`{m['io_ratio']:.2f}:1`**\n")
            doc.append(f"- **官方标称单价**：标称输入 `${m['prompt_p_per_m']:.4f}/M` | 标称输出 `${m['comp_p_per_m']:.4f}/M` | 缓存读取 `${m['cache_read_p_per_m']:.4f}/M`\n")
            if apps:
                app_items = [
                    f"{idx}. **{a['name']}**（流量份额 `{a.get('share_pct', 0.0):.1f}%`，累计 `{a['tokens']}` tokens）"
                    for idx, a in enumerate(apps[:2], 1)
                ]
                doc.append(f"- **偏好应用 (Top 2)**：{' | '.join(app_items)}\n")
            else:
                doc.append(f"- **偏好应用 (Top 2)**：无公开应用数据\n")
            top_tag = scenarios.get("top_tag")
            if top_tag:
                doc.append(f"- **优势细分场景**：`{top_tag}`\n")
            doc.append("\n")

        doc.append("---\n\n")

        # ==========================================
        # 三、 全平台任务场景大类与小类分布全景
        # ==========================================
        scenario_section = self.generate_task_scenarios_section()
        if scenario_section:
            doc.extend(scenario_section)

        # ==========================================
        # 四、 榜单指标与分析方法论
        # ==========================================
        doc.append("## 四、 榜单指标与分析方法论\n\n")
        doc.append("本报告核心指标的统计定义与计算口径如下：\n\n")
        doc.append("**1. 物理 Token 消耗与输入输出比（Input/Output Ratio）**：\n")
        doc.append("设模型在统计周期内的提示词输入 Token 为 \\(N_p\\)，模型生成输出 Token 为 \\(N_c\\)，总物理消耗 \\(T = N_p + N_c\\)。\n")
        doc.append("输入输出比 \\(r\\) 反映应用的典型交互模式：\n")
        doc.append("\\[ r = \\frac{N_p}{N_c} \\]\n\n")
        doc.append("在智能体协作、代码重构等长上下文场景中，通常呈现极高的 \\(r\\)（如 50:1 至 100:1 以上）。\n\n")
        doc.append("**2. 全平台消费份额占比（Platform Spend Share）**：\n")
        doc.append("数据来源于 OpenRouter 官方 7 天滚动支出排行榜接口（`GET /api/frontend/v1/rankings/models?metric=spend`）。接口返回的 `rankingMetricValue` 直接给出了过去 7 天内各模型占全平台开发者总支出的相对比例：\n")
        doc.append("\\[ \\text{Spend Share}_i = \\text{rankingMetricValue}_i \\times 100\\% \\]\n\n")
        doc.append("该份额直接反映模型在全平台商业变现与开发者真实付费预算层面的市场占有率。\n\n")
        doc.append("**3. 全平台厂商消费份额聚合方法（Vendor Spend Share Methodology）**：\n")
        doc.append("厂商消费份额基于模型研发/发布厂商口径（Model Creator），通过将全平台所有模型的 7 天滚动支出指标（`rankingMetricValue`）按模型命名空间（Permaslug 组织名前缀）归集累加得出：\n")
        doc.append("\\[ \\text{Spend Share}_{\\text{Vendor}} = \\sum_{m \\in \\text{Vendor}} \\text{rankingMetricValue}_m \\times 100\\% \\]\n\n")
        doc.append("该指标揭示了平台开发者在各基础大模型厂商之间的真实付费预算分配与商业生态格局。\n\n")
        doc.append("**4. 首选偏好应用流量份额（Top Apps Traffic Share）**：\n")
        doc.append("OpenRouter 官方模型详情页中的 Top Apps 展示了各客户端自接入以来的全量累计消耗。为消除绝对累计量与 7 天统计周期之间的量纲差异，报告取前序主要应用的流量比重计算相对偏好份额：\n")
        doc.append("\\[ \\text{Share}_i = \\frac{\\text{Tokens}_i}{\\sum_{k \\in \\text{Top Apps}} \\text{Tokens}_k} \\times 100\\% \\]\n\n")
        spend_win_days = self.task_spend.get("spend", {}).get("windowDays", 30)
        doc.append("**5. 优势细分场景与场景分布统计口径（Task Scenario Methodology）**：\n")
        doc.append(f"- **数据源与接口**：来自 OpenRouter 官方细分任务支出接口（`GET /api/frontend/v1/rankings/task-spend`）。\n")
        doc.append(f"- **统计时间窗口**：根据官方接口返回的 `windowDays: {spend_win_days}` 字段，统计基于**过去 {spend_win_days} 天滚动窗口（Rolling {spend_win_days}-Day Window）**的全平台美元消费支出（Spend Share），而非 Token 数量。\n")
        doc.append(f"- **指标作用与互补性**：核心榜单聚焦 7 天滚动用量以捕捉实时流量爆发；任务场景分布采用 30 天统计窗口以平滑短期偶然波动，揭示各模型在垂直领域生产环境与智能体流程中的中长期商业渗透与核心优势壁垒。各模型详细指标中的“优势细分场景”为该模型在过去 {spend_win_days} 天内取得市场份额第一（Top 1）的细分任务标签（若无公开细分数据则不展示）。\n\n")

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
    parser.add_argument("--end-date", type=str, default=None, help="End date of 7-day rolling window (YYYY-MM-DD)")
    args = parser.parse_args()

    generator = ModelReportGenerator(project_root=Path(args.project_root) if args.project_root else None)
    out_file = generator.generate_report(target_end_date=args.end_date)
    print(f"[+] Successfully generated report: {out_file}")


if __name__ == "__main__":
    main()
