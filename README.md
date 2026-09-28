# LLM Market Data

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Review: Passed](https://img.shields.io/badge/Code%20Review-Passed-brightgreen.svg)](https://github.com/alibaba/open-code-review)
[![Monitoring Since](https://img.shields.io/badge/Monitoring%20Since-2026--08--15-orange.svg)](#)

**LLM Market Data** 是一个自动化、轻量级的大语言模型（LLM）市场指标与使用数据聚合归档系统。本项目针对以 [OpenRouter](https://openrouter.ai/) 为代表的模型聚合市场，全天候自动化追踪模型定价、Token 消耗流速、应用分类排行榜、会话成本及历史每日使用排名，为 AI 市场分析、行业研究与定价决策提供可复现的结构化数据基础。

> 📅 **数据监控与归档起始时间**：
> * **历史每日排行归档**：始于 **2026-08-15**（支持按需自动增量回溯至平台成立起点 `2025-01-01`）
> * **全维度每日快照监测**：始于 **2026-09-28**（涵盖全量定价、应用排名、场景花费与会话成本）

---

## 🌟 核心特性 (Features)

* **📊 多维市场数据归档**：
  * `models`：全量模型元数据、上下文窗口、Prompt/Completion 实时价格快照。
  * `rankings_daily`：每日 Token 消耗总量与活跃度历史排行榜，支持时间序列分析。
  * `apps`：主流 AI 编码工具与 Agent（Cursor, Cline, Continue 等）的模型调用排名。
  * `task_spend`：按应用场景（Programming, Roleplay, Marketing 等）细分的模型市场份额。
  * `session_cost` & `performance` & `benchmarks`：单次会话预估成本、生成吞吐（TPS）与质量跑分快照。

* **⚡ 智能增量补全与配额保护**：
  * **自动断点补抓**：自动扫描自平台上线以来的缺失日期，按 30 天区间分块回填。
  * **请求预算管控**：单次运行严格受 `--max-requests` 配额限制，防止突发流量触发 API 封禁。
  * **容错与空数据保护**：API 瞬时异常不落盘错误快照；未结算日期保持缺失状态，下次调度自动重试。

* **🤖 自动化生产级工作流**：
  * **GitHub Actions**：定时无感运行并将新数据自动提交到仓库，零服务器维护成本。
  * **Cloudflare Worker 调度**：支持通过轻量 Serverless Worker 触发调度，解耦定时器与构建任务。
  * **安全合规**：API Key 统一由 GitHub Secrets 管理，入参强制隔离为环境变量，免疫 Shell 注入。

---

## 📁 数据存储结构 (Data Layout)

采集数据按统一规范以 JSON 格式落盘至 `data/openrouter/` 目录：

```text
data/openrouter/
├── apps/               # AI 编程工具与应用消耗快照 (YYYY-MM-DD.json)
├── benchmarks/         # 模型基准跑分评估快照 (YYYY-MM-DD.json)
├── models/             # 全量模型规格与定价快照 (YYYY-MM-DD.json)
├── performance/        # 模型首字延迟与生成吞吐测速 (YYYY-MM-DD.json)
├── rankings_daily/     # 历史每日 Token 排行榜分日明细 (YYYY-MM-DD.json)
├── session_cost/       # 典型交互会话成本估算 (YYYY-MM-DD.json)
└── task_spend/         # 各专业任务分类下的模型开销份额 (YYYY-MM-DD.json)
```

---

## 🚀 快速上手 (Quick Start)

### 1. 环境准备

需要 Python 3.9 或更高版本：

```bash
git clone https://github.com/pickmiu/llm-market-data.git
cd llm-market-data

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

复制环境变量模板：

```bash
cp .env.example .env
```

编辑 `.env` 文件填入您的 OpenRouter 凭据（公开榜单接口无需 Key，但每日历史排行数据需 API Key 授权）：

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
```

---

## 💻 命令行使用 (CLI Usage)

系统提供统一简洁的命令行工具 `cli.py`：

#### 全量增量同步（推荐日常使用）
自动扫描历史缺失日期并分批补全，同时获取今日各项最新快照：
```bash
python cli.py sync
```

#### 指定回溯天数与请求预算
只扫描最近 14 天的排行缺失，且本次运行最多消耗 10 次 API 调用：
```bash
python cli.py sync --lookback-days 14 --max-requests 10
```

#### 仅同步指定模块
支持 `models`, `rankings`, `apps`, `task_spend`, `session_cost`, `benchmarks`, `performance`：
```bash
# 仅更新今天的模型价格元数据
python cli.py sync --only models

# 仅更新编程工具与应用榜单
python cli.py sync --only apps
```

#### 强制刷新已存在的文件
```bash
python cli.py sync --force
```

---

## ⚙️ 自动化部署 (Automation & Deployment)

### 1. 配置 GitHub Actions Secrets
前往仓库 `Settings -> Secrets and variables -> Actions -> New repository secret`，添加：
* **Name**: `OPENROUTER_API_KEY`
* **Secret**: 您的 OpenRouter API 密钥

配置后，可在 Actions 页面通过 `workflow_dispatch` 手动触发运行，或等待定时调度。

### 2. （可选）Cloudflare Worker 定时与手动调度
在 `deploy/cloudflare/` 目录下提供了一个开箱即用的调度 Worker：
1. 仓库信息已默认预设为 `pickmiu/llm-market-data`，**仅需提供 GitHub 个人访问令牌 (`GITHUB_PAT`)**。
2. 配置环境变量：直接在 `deploy/cloudflare/wrangler.toml` 的 `[vars]` 中填写 `GITHUB_PAT`（或在 Cloudflare 控制台添加环境变量 `GITHUB_PAT`）。
3. 执行部署：
   ```bash
   cd deploy/cloudflare
   wrangler deploy
   ```
4. **调度触发方式**：
   * **自动定时**：每日 `00:30 UTC`（北京时间 08:30）通过 Cron 自动触发。
   * **手动调用（HTTP API）**：部署后可直接通过浏览器访问或调用 Worker URL 手动触发，支持自定义参数：
     ```bash
     # 浏览器打开或命令行 GET 请求
     curl https://<your-worker>.workers.dev/

     # 带参数手动触发（如最近 7 天、最大 20 次请求）
     curl "https://<your-worker>.workers.dev/?lookback_days=7&max_requests=20"

     # 或通过 POST JSON 触发
     curl -X POST https://<your-worker>.workers.dev/ \
       -H "Content-Type: application/json" \
       -d '{"lookback_days": 14, "max_requests": 30}'
     ```

---

## 🧪 自动化测试 (Testing)

项目配备了完善的单元测试集，覆盖网络重试、并发分块、数据归档幂等性及容错逻辑：

```bash
pytest -v
```

---

## 📄 开源许可证 (License)

本项目遵循 [MIT License](LICENSE) 开源协议。
