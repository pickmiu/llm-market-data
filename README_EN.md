# LLM Market Data

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Review: Passed](https://img.shields.io/badge/Code%20Review-Passed-brightgreen.svg)](https://github.com/alibaba/open-code-review)
[![Monitoring Since](https://img.shields.io/badge/Monitoring%20Since-2026--08--15-orange.svg)](#)

[**中文文档**](README.md) | [**English Documentation**](README_EN.md)

**LLM Market Data** is an automated, lightweight aggregation and archival pipeline for Large Language Model (LLM) market intelligence and usage metrics. Targeting the [OpenRouter](https://openrouter.ai/) multi-provider ecosystem, it continuously tracks model pricing, token consumption velocity, specialized task leaderboards, per-session cost dynamics, and historical daily rankings—providing reproducible, structured datasets for AI market research and pricing strategy.

> 📅 **Data Monitoring Coverage**:
> * **Historical Daily Rankings Archive**: Since **2026-08-15** (with automated incremental backfill support to platform inception `2025-01-01`).
> * **All-dimension Daily Snapshots**: Since **2026-09-28** (full model specs/pricing, coding tool apps, task spending categories, session costs).

---

## 🌟 Key Features

* **📊 Multi-dimensional Market Intelligence**:
  * `models`: Full model catalog with context length and real-time prompt/completion pricing.
  * `rankings_daily`: Daily token consumption volume and activity time series.
  * `apps`: Usage rankings across leading AI coding tools & autonomous agents (Cursor, Cline, Continue, etc.).
  * `task_spend`: Market share breakdowns across distinct tasks (Programming, Roleplay, Marketing, etc.).
  * `session_cost` & `performance` & `benchmarks`: Typical interactive session cost estimates, throughput (TPS), latency, and benchmark scores.

* **⚡ Smart Incremental Sync & Quota Guard**:
  * **Gap Detection**: Scans missing historical dates and backfills in bounded 30-day range chunks.
  * **Budget Bounding**: Each execution strictly enforces `--max-requests` quota limits to avoid rate-limiting.
  * **Zero-polluting Fault Tolerance**: Transient upstream errors skip disk-writing; unsettled dates remain unpersisted for subsequent retry.

* **🤖 Production-Ready Automation**:
  * **GitHub Actions**: Daily zero-maintenance workflow committing new data directly to the repo.
  * **Cloudflare Worker Dispatcher**: Serverless cron trigger and manual HTTP trigger endpoint.
  * **Security Hardened**: Secrets isolated within GitHub Secrets; CLI parameters sanitized against shell injection.

---

## 📁 Data Storage Layout

Collected datasets are structured in JSON format under `data/openrouter/`:

```text
data/openrouter/
├── apps/               # AI coding tools and apps leaderboard (YYYY-MM-DD.json)
├── benchmarks/         # Benchmark evaluation scores (YYYY-MM-DD.json)
├── models/             # Full model specifications and pricing (YYYY-MM-DD.json)
├── performance/        # Latency and throughput benchmarks (YYYY-MM-DD.json)
├── rankings_daily/     # Daily token rankings by date (YYYY-MM-DD.json)
├── session_cost/       # Estimated cost per session (YYYY-MM-DD.json)
└── task_spend/         # Model spending shares by task category (YYYY-MM-DD.json)
```

---

## 🚀 Quick Start

### 1. Requirements

Python 3.9 or higher:

```bash
git clone https://github.com/pickmiu/llm-market-data.git
cd llm-market-data

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration

Copy the environment template:

```bash
cp .env.example .env
```

Add your OpenRouter API key to `.env` (optional for public leaderboards, required for daily historical rankings):

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
```

---

## 💻 CLI Usage

Unified command-line interface via `cli.py`:

#### Full Incremental Synchronization (Recommended)
Automatically detects missing historical dates and updates today's latest snapshots:
```bash
python cli.py sync
```

#### Custom Date Window & Request Budget
Scan past 14 days with an upper limit of 10 API requests:
```bash
python cli.py sync --lookback-days 14 --max-requests 10
```

#### Sync Specific Module
Options: `models`, `rankings`, `apps`, `task_spend`, `session_cost`, `benchmarks`, `performance`:
```bash
# Update model pricing only
python cli.py sync --only models

# Update coding apps leaderboard only
python cli.py sync --only apps
```

#### Force Overwrite Existing Snapshots
```bash
python cli.py sync --force
```

---

## ⚙️ Automation & Deployment

### 1. GitHub Actions Setup
Go to repository `Settings -> Secrets and variables -> Actions -> New repository secret`, add:
* **Name**: `OPENROUTER_API_KEY`
* **Secret**: Your OpenRouter API key

The collector workflow runs automatically on schedule or via manual dispatch in the Actions tab.

### 2. Cloudflare Worker Scheduler
Ready-to-deploy Worker located in `deploy/cloudflare/`:
1. Repository is preset to `pickmiu/llm-market-data`. Only a GitHub Personal Access Token (`GITHUB_PAT`) is needed.
2. Add your token in `deploy/cloudflare/wrangler.toml` under `[vars]` (`GITHUB_PAT = "ghp_..."`) or via Cloudflare Dashboard.
3. Deploy:
   ```bash
   cd deploy/cloudflare
   wrangler deploy
   ```
4. **Trigger Methods**:
   * **Scheduled Cron**: Triggers daily at `00:30 UTC` (08:30 Beijing Time).
   * **Manual HTTP Trigger**: Trigger anytime via browser or API with optional custom parameters:
     ```bash
     curl https://<your-worker>.workers.dev/
     curl "https://<your-worker>.workers.dev/?lookback_days=7&max_requests=20"
     ```

---

## 🧪 Testing

Comprehensive test suite verifying retry behavior, concurrency chunking, and idempotency:

```bash
pytest -v
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
