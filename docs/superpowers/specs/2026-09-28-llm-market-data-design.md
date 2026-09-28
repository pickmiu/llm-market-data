# LLM Market Data Analysis - System Design Specification

## 1. Overview & Objectives

本项目旨在构建一个轻量、模块化、可扩展的大模型市场数据分析系统（主要使用 Python）。首期以 **OpenRouter** 作为核心数据源，对主流大语言模型的市场份额演变、厂商消费分布、细分场景集中度以及厂商策略效果进行量化评估。

### 核心分析目标
1. **热门模型份额变化**：追踪 Top 模型的真实 Token 消耗量、在整体市场中的占比及时间演变趋势。
2. **细分应用与场景份额**：按模型特性/标签（如代码模型 Code Agent、推理模型、多模态）细分各领域的市场渗透率。
3. **各厂商消费金额占比（GMV 估算）**：结合模型调用量与输入/输出 Token 单价，推算各主流厂商（如 OpenAI、Anthropic、Meta、Google 等）的商业流水份额变化。
4. **厂商策略评估**：针对重大市场事件（例如某厂商发布能力相近、价格折半的新模型，或主动降价），对比事件发生前后 N 天的调用量份额与营收变化，评估“以价换量”策略是否有效。
5. **一键自动化流水线**：提供简单直观的 CLI，支持一键执行抓取、留存快照、计算分析并自动导出图文并茂的分析报告（Markdown/HTML）。

---

## 2. 系统架构与目录结构

采用**轻量直接流架构**，避免沉重的数据库维护成本，以接口数据为核心，配合本地快照文件作为备份与重放机制。

```text
llm-market-data/
├── sources/                   # 多数据源目录（未来可扩展不同平台）
│   └── openrouter/            # OpenRouter 专属适配器
│       ├── __init__.py
│       ├── README.md          # 详细记录 OpenRouter 开放数据项及分析价值
│       ├── client.py          # 负责向 OpenRouter 发起 HTTP 请求
│       └── parser.py          # 将接口原始返回清洗整合为标准 Pandas DataFrame
├── analysis/                  # 核心数据分析模块
│   ├── __init__.py
│   ├── share.py               # 热门模型份额与细分类别（Code Agent等）份额
│   ├── spend.py               # 消费金额与厂商营收份额估算 (Token × Pricing)
│   └── strategy.py            # 策略对比评估（新模型发布/调价前后窗口弹性分析）
├── reports/                   # 报告与可视化
│   ├── __init__.py
│   ├── charts.py              # 图表绘制（趋势折线图、厂商堆叠图、份额饼图）
│   ├── generator.py           # 自动化报告组装与 Markdown 导出
│   └── output/                # 报告与生成图表的输出目录（按日期或任务存放）
├── data/                      # 统一存放数据快照
│   └── openrouter/            # 存放原始抓取的 JSON 快照文件
├── tests/                     # 单元与集成测试
│   ├── __init__.py
│   ├── test_client.py
│   ├── test_parser.py
│   └── test_analysis.py
├── .env.example               # 环境变量模板（OPENROUTER_API_KEY）
├── .gitignore                 # 忽略快照大型文件、输出与敏感配置
├── requirements.txt           # 基础轻量依赖
└── cli.py                     # 统一命令行入口
```

---

## 3. 数据源适配：OpenRouter 规格与设计

### 3.1 开放数据项定义 (`sources/openrouter/README.md`)
OpenRouter 提供了两个核心公开接口：
1. **模型元数据接口 (`/api/v1/models`)**
   - **请求方式**：`GET https://openrouter.ai/api/v1/models`
   - **权限要求**：公开，支持无 Key 或携带 Bearer Key。
   - **核心字段**：
     - `id`: 模型唯一标识符（例如 `openai/gpt-4o-mini`, `anthropic/claude-3.5-sonnet`）。
     - `name`: 友好显示名称。
     - `pricing`: 包含 `prompt`（输入单价）和 `completion`（输出单价），单位为美元/Token。
     - `context_length`: 最大上下文长度。
     - `architecture`: 模型架构信息（模态 modality、分词器 tokenizer 等）。
     - `description`: 描述信息（可用于提取标签如 code agent, reasoning 等）。
2. **每日调用排行接口 (`/api/v1/datasets/rankings-daily`)**
   - **请求方式**：`GET https://openrouter.ai/api/v1/datasets/rankings-daily`
   - **权限要求**：必须在 Header 包含 `Authorization: Bearer <API_KEY>`。
   - **请求参数**：`start_date`（如 `2026-08-01`）、`end_date`（如 `2026-08-31`）。
   - **核心字段**：按天返回 Top 50 模型的调用量统计（`prompt_tokens`, `completion_tokens`, `total_tokens`）以及针对其余长尾模型的 `other` 汇总行。
   - **频次限制**：30 次/分钟，500 次/天。

### 3.2 快照归档策略 (`data/openrouter/`)
- 抓取的数据原始 JSON 直接存放在 `data/openrouter/` 下，文件命名格式：
  - `YYYY-MM-DD_models.json`
  - `YYYY-MM-DD_rankings_daily.json`
- **缓存与防重抓机制**：执行时优先检查今日快照是否已存在。若存在且未指定 `--force`，则直接加载本地快照，减少对平台请求频率与网络消耗。

---

## 4. 核心分析模块设计 (`analysis/`)

### 4.1 数据整合与标准结构 (`parser.py`)
解析器将模型价格信息与每日调用量合并为宽表 DataFrame：
- `date`: 日期（YYYY-MM-DD）
- `model_id`: 模型 ID
- `vendor`: 厂商名称（从 `model_id` 提取前缀，如 `openai`, `anthropic`, `deepseek`）
- `prompt_tokens`: 输入 Token 数量
- `completion_tokens`: 输出 Token 数量
- `total_tokens`: 总 Token 消耗量
- `prompt_price`: 每 Token 输入单价
- `completion_price`: 每 Token 输出单价
- `est_prompt_spend`: 估算输入消费 (`prompt_tokens * prompt_price`)
- `est_completion_spend`: 估算输出消费 (`completion_tokens * completion_price`)
- `est_total_spend`: 估算总花费 (`est_prompt_spend + est_completion_spend`)
- `category`: 分类标签（基于模型特征打标，如 `Code Agent`, `General Chat`, `Reasoning`）

### 4.2 核心指标算法
1. **模型份额 (`analysis/share.py`)**：
   - 每日市场总 Token: $T_{total}(d) = \sum_{m} T_m(d)$
   - 模型份额: $Share_m(d) = \frac{T_m(d)}{T_{total}(d)}$
   - 计算 7 天 / 30 天滑动平均与环比涨跌幅。
2. **应用/场景份额 (`analysis/share.py`)**：
   - 聚合判定为特定标签（如包含 `coder`, `deepseek-coder`, `qwen-coder` 等的编程模型）的整体 Token 占比：
     $CategoryShare_c(d) = \frac{\sum_{m \in c} T_m(d)}{T_{total}(d)}$
3. **厂商消费份额 (`analysis/spend.py`)**：
   - 厂商每日营收估算: $Spend_v(d) = \sum_{m \in v} est\_total\_spend_m(d)$
   - 厂商金额份额占比: $SpendShare_v(d) = \frac{Spend_v(d)}{\sum_v Spend_v(d)}$
4. **策略弹性评估 (`analysis/strategy.py`)**：
   - 针对指定事件（模型发布/调价），以事件日期 $t_0$ 为界，提取窗口 $[t_0 - N, t_0 - 1]$ 与 $[t_0 + 1, t_0 + N]$。
   - 对比指标：
     - 前后平均日 Token 消耗量对比：$\Delta Token = \frac{\overline{Token}_{post} - \overline{Token}_{pre}}{\overline{Token}_{pre}}$
     - 前后市场份额对比：$\Delta Share = \overline{Share}_{post} - \overline{Share}_{pre}$
     - 前后总消费流水对比：$\Delta Spend = \frac{\overline{Spend}_{post} - \overline{Spend}_{pre}}{\overline{Spend}_{pre}}$
   - 结论自动生成逻辑：例如若价格下降 50%，而 $\Delta Token < 100\%$，则输出“以价换量未能实现规模翻倍，整体流水出现收缩”；反之若 $\Delta Token \ge 100\%$，则判定为“有效驱动了规模扩张”。

---

## 5. 报告生成与可视化 (`reports/`)

### 5.1 图表生成 (`reports/charts.py`)
利用 Matplotlib / Seaborn 渲染清晰美观的图片，保存于 `reports/output/images/`：
- `model_share_trend.png`: Top 10 模型市场份额时间走势折线图
- `vendor_spend_distribution.png`: 各厂商消费金额份额饼图/堆叠面积图
- `category_share_trend.png`: 场景（如 Code Agent）渗透率变化趋势
- `strategy_event_impact.png`: 关键策略事件前后窗口对比柱状图

### 5.2 报告输出 (`reports/generator.py`)
自动导出 Markdown 与轻量 HTML 格式报告（`reports/output/report_YYYYMMDD.md`），结构包含：
1. **执行概要与核心发现**
2. **热门模型份额排行及异动表**
3. **细分场景（Code Agent 等）发展态势**
4. **各厂商消费金额与 GMV 集中度**
5. **策略案例复盘分析与结论建议**
6. **图表附件与数据附录**

---

## 6. 命令行接口设计 (`cli.py`)

提供简洁易用的统一交互命令：

```bash
# 1. 一键全自动模式（抓取数据 + 保存快照 + 分析计算 + 导出报告）
python cli.py auto --days 30

# 2. 单独抓取并留存快照
python cli.py fetch --source openrouter --days 30 [--force]

# 3. 基于本地已存快照执行分析并导出报告（支持完全离线）
python cli.py report --from-snapshot --output reports/output/my_report.md

# 4. 指定策略分析案例
python cli.py strategy --target-model "openai/gpt-4o-mini" --event-date "2024-07-18" --window 14
```

---

## 7. 错误处理与离线降级 (Resilience)

1. **API Key 缺失友好提示**：若未检测到 `OPENROUTER_API_KEY`，引导用户设置 `.env` 文件。
2. **限流保护**：若触发 429 请求超限，增加指数退避重试（Exponential Backoff）。
3. **离线重放**：当接口连接失败或没有外部网络时，自动检测 `data/openrouter/` 下是否已有历史快照，若有则提示切换至离线模式进行分析，保证报告生成流程不中断。

---

## 8. 测试策略

1. **单元测试 (`tests/`)**：
   - `test_client.py`：使用 Mock 模拟 OpenRouter 返回，验证参数拼装与错误状态捕获。
   - `test_parser.py`：测试模型价格与每日 Token 关联清洗，验证空值和异常值容错。
   - `test_analysis.py`：测试份额计算、厂商金额统计与策略对比函数的准确度。
2. **端到端测试**：
   - 验证 `cli.py auto` 在样例数据下的全流程执行，确保成功输出图表与 Markdown 报告。
