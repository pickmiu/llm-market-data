# OpenRouter 大模型市场数据采集与持久化系统设计规范

## 1. 目标与范围 (Overview & Scope)

本项目构建一个轻量、模块化、高可用的 LLM 市场数据自动采集与持久化系统。首期聚焦于 **OpenRouter** 数据生态，实现数据的自动归档、智能限流补抓与定时调度。

### 核心范围
1. **多维度数据采集（以接口为主，去重互补）**：
   - **官方 API 接口（核心权威数据源）**：获取模型元数据与定价快照（`/api/v1/models`）及每日模型 Token 消耗排行（`/api/v1/datasets/rankings-daily`）。接口已有的模型数据绝不在网页端重复抓取。
   - **网页轻量爬虫（仅抓取接口未开放的独有数据）**：仅抓取 OpenRouter 网页端公开的 **Apps 与 Coding Agents 排行**（如 Hermes Agent、Cline、Kilo Code 等应用维度的日/周/月 Token 与请求量排行榜），补全生态链数据。
2. **全自动历史回溯与严格限流**：
   - 自动回溯至平台历史数据起点（官方数据集底线 2025-01-01），自动比对本地数据缺失日期并分批补齐。
   - 严格遵循 OpenRouter 速率限制（30 次/分钟、500 次/天），内置请求节流（2.5 秒/次）与指数退避重试，支持单次批次预算上限，天然支持断点续传。
3. **精准定时调度与 GitOps 持久化**：
   - 结合 OpenRouter 前端“最近完整日（most recent complete day）”于 UTC 00:00 封账的特性，使用 Cloudflare Worker 定时器（Cron Trigger）在每日 UTC 00:30（北京时间 08:30）准点触发。
   - GitHub Actions 响应触发并执行数据拉取与校验，自动将更新的 JSON 数据提交并推送至 Git 仓库的 `data/` 目录中。
4. **范围排除 (Out of Scope)**：
   - 报告与图表生成模块（Markdown 日/周/月报与可视化）推迟至第二阶段进行，第一阶段专注夯实数据持久化底座。

---

## 2. 系统架构与目录结构

采用**纯 GitOps + 无数据库轻量直存**架构，零第三方数据库运维成本，快照透明可追溯。

```text
llm-market-data/
├── sources/
│   └── openrouter/
│       ├── __init__.py
│       ├── client.py             # OpenRouter API 客户端（models 与 rankings-daily，含节流与重试）
│       ├── crawler.py            # 网页独有数据提取器（从 SSR 提取接口没有的 Apps/Agents 排行）
│       └── sync.py               # 缺失日期扫描、限流配额控制与增量补抓调度引擎
├── data/                         # 持久化数据快照存储根目录
│   └── openrouter/
│       ├── models/               # YYYY-MM-DD.json（模型元数据与定价快照，来自 API）
│       ├── rankings_daily/       # YYYY-MM-DD.json（官方每日 Top 50 模型 Token 调用量明细，来自 API）
│       ├── apps/                 # YYYY-MM-DD.json（Coding Agents / Apps 排行快照，来自公开前端 API）
│       ├── task_spend/           # YYYY-MM-DD.json（Top models by task: 各场景与任务份额快照，来自公开前端 API）
│       ├── session_cost/         # YYYY-MM-DD.json（Cost per session: 各 Coding Agent 会话轮次开销快照，来自公开前端 API）
│       └── benchmarks/           # YYYY-MM-DD.json（Artificial Analysis & Dev Arena 基准评测与加权价格快照，来自公开前端 API）
├── deploy/
│   └── cloudflare/
│       ├── wrangler.toml         # Cloudflare Worker Cron Trigger 配置文件
│       └── worker.js             # 定时触发 GitHub Actions workflow_dispatch 的无服务器代码
├── .github/
│   └── workflows/
│       └── collector.yml         # GitHub Actions 自动化执行与 Git 提交推送工作流
├── tests/                        # 自动化测试
│   ├── __init__.py
│   ├── test_client.py            # API 客户端与重试测试
│   ├── test_crawler.py           # 前端数据解析测试
│   └── test_sync.py              # 缺失补抓算法与节流控制测试
├── .env.example                  # 环境变量示例（OPENROUTER_API_KEY）
├── .gitignore                    # 忽略临时文件、缓存
├── requirements.txt              # 核心依赖（仅需 requests）
└── cli.py                        # 统一命令行交互入口
```

---

## 3. 数据规格与存储规范 (`data/openrouter/`)

### 3.1 模型元数据快照 (`models/YYYY-MM-DD.json`)
- **来源**：`GET https://openrouter.ai/api/v1/models`
- **权限**：公开免鉴权
- **存储内容**：包含当天抓取时间戳 `fetched_at` 以及所有模型的完整元数据列表（过滤/保留关键字段：`id`, `name`, `pricing` (`prompt`, `completion`), `context_length`, `architecture`, `description`）。

### 3.2 每日调用排行 (`rankings_daily/YYYY-MM-DD.json`)
- **来源**：`GET https://openrouter.ai/api/v1/datasets/rankings-daily?start_date=...&end_date=...`
- **权限**：需请求头 `Authorization: Bearer <OPENROUTER_API_KEY>`
- **字段结构**：
  ```json
  {
    "date": "2026-09-27",
    "fetched_at": "2026-09-28T00:30:15Z",
    "as_of": "2026-09-28T00:15:00Z",
    "data": [
      {
        "date": "2026-09-27",
        "model_permaslug": "openai/gpt-4o-mini",
        "prompt_tokens": 12500000000,
        "completion_tokens": 3400000000,
        "total_tokens": 15900000000
      }
    ]
  }
  ```

### 3.3 网页端独有快照：应用与 Agent 排行 (`apps/YYYY-MM-DD.json`)
- **设计原则（去重互补）**：严格以官方 API 接口数据为基准；接口已有的模型排行数据绝不从网页端重复抓取。
- **数据来源**：直接通过公开 REST 接口 `GET https://openrouter.ai/api/frontend/v1/rankings/apps` 获取纯 JSON（免鉴权）。
- **覆盖范围**：包含 `day`（日榜）、`week`（周榜）、`month`（月榜）三个维度的应用排行。
- **核心数据项**：
  - `rank`: 应用排名
  - `app_id`: 应用唯一 ID
  - `title`: 应用名称（例如 Hermes Agent、Cline、Kilo Code、Claude Code 等）
  - `categories`: 分类标签（如 `personal-agent`, `cli-agent`, `ide-extension` 等，直接映射 Coding Agents 榜单）
  - `total_tokens`: 该周期内处理的总 Token 数量
  - `total_requests`: 调用总请求次数
  - `description`: 工具简介描述

### 3.4 任务场景细分快照：Top Models by Task (`task_spend/YYYY-MM-DD.json`)
- **来源**：直接通过公开 REST 接口 `GET https://openrouter.ai/api/frontend/v1/rankings/task-spend` 获取纯 JSON（免鉴权）。
- **覆盖范围**：同时包含 `spend`（金额份额）与 `tokens`（Token 份额）两大维度。
- **核心数据项**：
  - `macroCategories`: 四大宏观任务领域分布（General 31.2%, Agent 30.0%, Code 29.1%, Data 9.7%）
  - `tasks`: 各细分任务（Classification, Workflow Execution, Code Generation, Debugging, Multi-step Planning 等）在总大盘中的占比
  - `models`: 各任务下排名前列的模型标识、具体份额占比 (`share`) 与近期点位变动 (`deltaPp`)
- **归档格式**：保存为每日完整快照 `data/openrouter/task_spend/YYYY-MM-DD.json`。

### 3.5 Coding Agent 会话开销快照：Cost Per Session (`session_cost/YYYY-MM-DD.json`)
- **来源**：直接通过公开 REST 接口 `GET https://openrouter.ai/api/frontend/v1/rankings/session-cost` 获取纯 JSON（免鉴权）。
- **指标含义**：展示主流 Coding Agent（Hermes Agent, Claude Code, Kilo Code, Codex 等）在不同会话长度下的单会话中位数花费（美元）。
- **核心数据项**：
  - `windowDays`: 统计时间窗口（默认最近 30 天）
  - `windowEnd`: 统计窗口截止时间
  - `harnesses`: 各 Coding Agent 运行容器（如 `appId`: 3067167 为 Hermes Agent，2627404 为 Claude Code，2262242 为 Kilo Code，2668297 为 Codex 等）
    - `models`: 各支持模型的会话长度分桶开销数据：
      - `single` (1 turn): 单轮交互典型开销
      - `short` (2-9 turns): 短交互典型开销
      - `core` (10-49 turns): 常规核心交互典型开销
      - `long` (50+ turns): 深度长任务典型开销
- **归档格式**：保存为每日完整快照 `data/openrouter/session_cost/YYYY-MM-DD.json`。

### 3.6 模型基准测评与性价比快照：Benchmarks (`benchmarks/YYYY-MM-DD.json`)
- **来源**：直接通过公开 REST 接口 `GET https://openrouter.ai/api/frontend/v1/rankings/benchmarks` 获取纯 JSON（免鉴权）。
- **指标含义**：整合权威第三方评测机构（如 Artificial Analysis 和 Dev Arena）的多维智力、编码、智能体能力指数，以及对应的模型加权输入价格。
- **核心数据项**：
  - `aaData` (Artificial Analysis 权威指数)：
    - `intelligence`: 综合智力指数排行榜（如 Claude Opus 5.5: 57.6, Claude Fable 5.1: 53.4, Qwen3.8 Max: 53.4 等）
    - `coding`: 代码生成与编程能力评测指数
    - `agentic`: 智能体与工具调用评测指数
  - `daData` (Dev Arena 评测分项)：涵盖 website, 3d, dataviz, gamedev 等领域的 Arena Elo 评分
  - `weightedInputPrices`: 各模型在 OpenRouter 上的实际加权输入成本（$/1M tokens，散点图 X 轴核心基准）
  - `costPerRequest`: 各模型的单次请求成本分布
- **归档格式**：保存为每日完整快照 `data/openrouter/benchmarks/YYYY-MM-DD.json`。

### 3.7 幂等规则
- 检查目标 JSON 文件：若已存在且为非空合法 JSON，直接跳过；
- 支持传入 `--force` 参数以允许重新覆盖（例如手动强制刷新特定日期）。

---

## 4. 采集器与智能限流补抓引擎 (`sync.py`)

### 4.1 限制指标与防护设计
- **官方硬限**：30 次请求/分钟，500 次请求/天。
- **主动节流 (Pacing)**：单次 HTTP 请求后强制等待 **2.5 秒**（即最高 24 次/分钟，留足 20% 安全余量）。
- **重试机制 (Backoff)**：遇到 HTTP 429 或 5xx 状态码，执行指数退避重试（最多 3 次，间隔 5s, 10s, 20s）。若重试仍失败，安全中止当前批次并保留已落盘数据。

### 4.2 缺失检测与全自动历史回溯算法
1. **自动回溯至平台起点 (Inception Floor)**：
   - 官方数据集底线：OpenRouter `rankings-daily` 起始日期为 **2025-01-01**（早于此日期的请求会自动截断）。
   - 自动回溯区间：默认从**昨天（UTC）**一路回溯至平台底线 **2025-01-01**（无需人工指定天数，支持通过 `--start-date` 覆盖自定义底线）。
2. **扫描与缺失分块 (Chunking)**：
   - 遍历 `[2025-01-01, Yesterday]` 区间内所有日期；
   - 筛选出本地 `data/openrouter/rankings_daily/YYYY-MM-DD.json` 缺失或为空的日期；
   - 若本地已完整补齐至平台起点，则日常运行仅需抓取昨天的 1 天数据；
   - 若存在缺失，利用 OpenRouter API 原生支持 `start_date` 与 `end_date` 区间查询的特性，将连续缺失日期按月/时间段切分为批次块（例如每块 30 天，单次请求即可获取一个月的全部日排行），或者逐日补抓。
3. **分拆落盘与幂等性**：
   - 批量请求返回的列表按每条记录的 `date` 字段自动分组，分别独立写入对应的 `data/openrouter/rankings_daily/YYYY-MM-DD.json`；
   - 每次写入前校验文件有效性，已存在的有效文件自动跳过，实现彻底的增量同步。
4. **批次限额控制 (Budget Guard)**：
   - 单次运行支持设置最大请求数上限 `max_requests`（默认 `40` 次，相当于即便逐日抓取也能补 40 天，若按 30 天区间块批量抓取则单次即可回溯数百天）；
   - 耗时严格控制在 CI 超时安全阈值内，未补全部分下次调度自动接续。

---

## 5. 定时调度与自动化流水线

### 5.1 调度时机契约
- **时区标准**：UTC。
- **调度周期**：每日 UTC 00:30（对应北京时间 08:30）。
- **设计依据**：OpenRouter 自然日于 UTC 00:00 结束，缓冲 30 分钟后前一天完整数据完成沉淀，前端 `Today` 标签与 API `rankings-daily` 完全同步。

### 5.2 Cloudflare Worker 调度实现 (`deploy/cloudflare/`)
- **配置 (`wrangler.toml`)**：
  ```toml
  name = "llm-market-data-scheduler"
  main = "worker.js"
  compatibility_date = "2026-09-28"

  [triggers]
  crons = ["30 0 * * *"]
  ```
- **核心逻辑 (`worker.js`)**：
  在 `scheduled` 事件中，向 GitHub API 发送 POST 请求：
  - **URL**: `https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows/collector.yml/dispatches`
  - **Headers**:
    - `Authorization: Bearer <GITHUB_PAT>`
    - `Accept: application/vnd.github.v3+json`
    - `User-Agent: CF-Worker-Scheduler`
  - **Payload**: `{"ref": "main", "inputs": {"lookback_days": "90", "max_requests": "40"}}`
- **Secrets 管理**：在 Cloudflare Dashboard 或 Wrangler 中绑定 `GITHUB_PAT`（具有 actions 读写权限的个人访问令牌）和 `GITHUB_REPO`。

### 5.3 GitHub Actions 工作流 (`.github/workflows/collector.yml`)
- **触发条件**：
  - `workflow_dispatch`（接收 Cloudflare 调用或在网页上手动触发，支持自定义 `lookback_days` 和 `max_requests`）；
  - `schedule: - cron: '30 1 * * *'`（可选原生定时器，作为双保险兜底）。
- **执行阶段**：
  1. `actions/checkout@v4`：获取仓库最新代码与历史 `data/` 目录；
  2. `actions/setup-python@v5`：配置 Python 3.11 环境；
  3. 安装极简依赖：`pip install requests`；
  4. 执行同步脚本：
     ```bash
     python cli.py sync \
       --lookback-days "${{ github.event.inputs.lookback_days || '90' }}" \
       --max-requests "${{ github.event.inputs.max_requests || '40' }}"
     ```
  5. 检查与提交更改：
     - 若 `git status --porcelain data/` 有新增文件，配置 Git 机器人提交并推送到 `main`：
       `git commit -m "chore(data): auto-sync openrouter data [skip ci]"`
       `git push origin main`
     - 若无文件变动，直接退出，不创建空 commit。

---

## 6. CLI 命令行设计 (`cli.py`)

提供简单直接的统一交互命令：

```bash
# 1. 默认常规同步（自动抓取最新 models、web_rankings，并限流补齐缺失的 rankings_daily）
python cli.py sync

# 2. 自定义回溯深度与单次配额
python cli.py sync --lookback-days 30 --max-requests 50

# 3. 指定固定起止日期补抓
python cli.py sync --start-date 2026-08-01 --end-date 2026-08-31

# 4. 强制刷新已存在的数据
python cli.py sync --lookback-days 7 --force

# 5. 仅执行单个维度的采集（便于本地排查与测试）
python cli.py sync --only models
python cli.py sync --only rankings
python cli.py sync --only web
```

---

## 7. 测试策略与验收标准

### 7.1 单元测试 (`tests/`)
1. **`test_client.py`**：
   - 验证 HTTP 状态码 200 时的正确解析与返回；
   - 验证遇到 429/500 时指数退避重试逻辑及最终异常抛出；
   - 验证请求头 `Authorization` 的正确拼接。
2. **`test_crawler.py`**：
   - 使用静态 HTML 模拟 OpenRouter 网页，验证对 Next.js SSR 预渲染数据解析的健壮性；
   - 验证遇到网络异常或解析失败时优雅降级（不阻断 API 主流程）。
3. **`test_sync.py`**：
   - 模拟本地目录存在部分日期文件，验证缺失日期识别算法；
   - 验证倒序（由近及远）排序与 `max_requests` 截断逻辑；
   - 验证节流间隔执行与 `--force` 行为。

### 7.2 端到端集成验证
- 在配置好本地 `.env` 的情况下执行 `python cli.py sync --lookback-days 3`，确认生成相应日期的 JSON 文件且结构符合规范；
- 验证 GitHub Actions 工作流在 Dry-run 下顺利完成检出、同步与无变更跳过逻辑。
