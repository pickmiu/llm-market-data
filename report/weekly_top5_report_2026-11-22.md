# weekly_top5_report_2026-11-22

- **统计周期**：`2026-11-16` 至 `2026-11-22`（连续完整 7 天）  
- **数据生成时间**：`2026-11-23 00:31:22`  

---

## 一、 核心榜单数据（榜单与首选应用）

### 1. Token 物理使用量前 5 模型

| 排名 | 模型名称 | 7天 Token 消耗 | 全平台消费份额占比 | I/O 比率 | 标称单价 (入/出, $/M) | 实际单价 (入/出, $/M) | 首选偏好应用 (Top 1 份额) |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---|
| 1 | DeepSeek: DeepSeek V4.1 Flash 1017 | **65.077 T** | **4.68%** | 70.3:1 | $0.1500 / $0.6000 | $0.0200 / $0.1500 | Hermes Agent (44.2%) |
| 2 | DeepSeek: DeepSeek V4.1 Flash | **15.355 T** | **2.35%** | 42.1:1 | $0.0498 / $0.1992 | $0.0200 / $0.1800 | Hermes Agent (44.2%) |
| 3 | Z.ai: GLM 5.3 Flash | **12.235 T** | **2.33%** | 38.3:1 | $0.0399 / $0.0784 | $0.0459 / $0.0105 | Claude Code (45.5%) |
| 4 | Tencent: Hy4 flash | **10.215 T** | **0.21%** | 128.4:1 | $0.0350 / $0.1405 | $0.0350 / $0.1405 | Hermes Agent (75.8%) |
| 5 | OpenAI: GPT-6 Luna | **8.396 T** | **1.52%** | 27.9:1 | $0.1000 / $0.5000 | $0.0500 / $0.2500 | Codex (56.9%) |

### 2. 全平台消费份额前 5 模型

| 排名 | 模型名称 | 全平台消费份额占比 | 7天 Token 消耗 | I/O 比率 | 标称单价 (入/出, $/M) | 实际单价 (入/出, $/M) | 首选偏好应用 (Top 1 份额) |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---|
| 1 | Anthropic: Claude Opus 5.5 | **14.11%** | 6.983 T | 119.5:1 | $4.0000 / $20.0000 | $4.0000 / $20.0000 | Claude Code (79.8%) |
| 2 | Google: Gemini 4 Carbon | **5.92%** | 2.425 T | 42.4:1 | $2.0000 / $10.0000 | $1.0000 / $5.0000 | Hermes Agent (25.5%) |
| 3 | Anthropic: Claude Sonnet 5.5 | **5.39%** | 2.798 T | 62.1:1 | $2.0000 / $10.0000 | $2.0000 / $10.0000 | Claude Code (52.8%) |
| 4 | MoonshotAI: Kimi K3.1 Pro | **4.78%** | 4.067 T | 132.3:1 | $0.2403 / $8.4023 | $0.1900 / $8.9276 | Portkey AI (36.7%) |
| 5 | DeepSeek: DeepSeek V4.1 Flash 1017 | **4.68%** | 65.077 T | 70.3:1 | $0.1500 / $0.6000 | $0.0200 / $0.1500 | Hermes Agent (44.2%) |

### 3. 全平台消费份额前 5 厂商

| 排名 | 厂商名称 | 7天全平台消费份额占比 | 7天 Token 消耗总量 | 主力拉动模型 (单模型消费份额) |
|:---:|:---|:---:|:---:|:---|
| 1 | Anthropic | **30.18%** | 14.656 T | Claude Opus 5.5 (14.11%) |
| 2 | Google | **19.12%** | 9.666 T | Gemini 4 Carbon (5.92%) |
| 3 | OpenAI | **17.56%** | 17.559 T | GPT-6 Astra (3.94%) |
| 4 | DeepSeek (深度求索) | **9.79%** | 86.735 T | DeepSeek V4.1 Flash 1017 (4.68%) |
| 5 | 月之暗面 (Moonshot AI) | **7.27%** | 5.265 T | Kimi K3.1 Pro (4.78%) |

---

## 二、 各模型详细指标数据

### 1. Token 使用量前 5 模型指标

#### 1.1 DeepSeek: DeepSeek V4.1 Flash 1017 (`deepseek/deepseek-v4.1-flash-20261017`)

- **总消耗 Token**：`65,077,293,847,944` (65.077T Tokens)
- **全平台消费份额占比**：`4.68%`
- **Token 输入/输出**：输入 Prompt `64,164,714,565,388` | 输出 Completion `912,579,282,556` | **I/O 比例：`70.31:1`**
- **官方标称单价**：标称输入 `$0.1500/M` | 标称输出 `$0.6000/M` | 缓存读取 `$0.0030/M`
- **供应商实际最低单价**：实际输入 `$0.0200/M` (OpenInference) | 实际输出 `$0.1500/M` (Sail Research) | 活跃供应商端点数：`34` 家
- **偏好应用 (Top 2)**：1. **Hermes Agent**（流量份额 `44.2%`，累计 `8.35T` tokens） | 2. **Claude Code**（流量份额 `20.1%`，累计 `3.80T` tokens）
- **优势细分场景**：`software.security_assessment`

#### 1.2 DeepSeek: DeepSeek V4.1 Flash (`deepseek/deepseek-v4.1-flash-20260910`)

- **总消耗 Token**：`15,355,175,576,717` (15.355T Tokens)
- **全平台消费份额占比**：`2.35%`
- **Token 输入/输出**：输入 Prompt `14,998,962,892,156` | 输出 Completion `356,212,684,561` | **I/O 比例：`42.11:1`**
- **官方标称单价**：标称输入 `$0.0498/M` | 标称输出 `$0.1992/M` | 缓存读取 `$0.0010/M`
- **供应商实际最低单价**：实际输入 `$0.0200/M` (OpenInference) | 实际输出 `$0.1800/M` (Decart) | 活跃供应商端点数：`41` 家
- **偏好应用 (Top 2)**：1. **Hermes Agent**（流量份额 `44.2%`，累计 `8.35T` tokens） | 2. **Claude Code**（流量份额 `20.1%`，累计 `3.80T` tokens）
- **优势细分场景**：`software.security_assessment`

#### 1.3 Z.ai: GLM 5.3 Flash (`z-ai/glm-5.3-flash-20260826`)

- **总消耗 Token**：`12,235,287,918,368` (12.235T Tokens)
- **全平台消费份额占比**：`2.33%`
- **Token 输入/输出**：输入 Prompt `11,924,294,898,857` | 输出 Completion `310,993,019,511` | **I/O 比例：`38.34:1`**
- **官方标称单价**：标称输入 `$0.0399/M` | 标称输出 `$0.0784/M` | 缓存读取 `$0.0300/M`
- **供应商实际最低单价**：实际输入 `$0.0459/M` (Relace) | 实际输出 `$0.0105/M` (OpenInference) | 活跃供应商端点数：`34` 家
- **偏好应用 (Top 2)**：1. **Claude Code**（流量份额 `45.5%`，累计 `7.72T` tokens） | 2. **Portkey AI**（流量份额 `20.8%`，累计 `3.54T` tokens）
- **优势细分场景**：`data.evaluation`

#### 1.4 Tencent: Hy4 flash (`tencent/hy4-flash-20261116`)

- **总消耗 Token**：`10,214,736,573,544` (10.215T Tokens)
- **全平台消费份额占比**：`0.21%`
- **Token 输入/输出**：输入 Prompt `10,135,788,445,822` | 输出 Completion `78,948,127,722` | **I/O 比例：`128.39:1`**
- **官方标称单价**：标称输入 `$0.0350/M` | 标称输出 `$0.1405/M` | 缓存读取 `$0.0015/M`
- **供应商实际最低单价**：实际输入 `$0.0350/M` (Tencent) | 实际输出 `$0.1405/M` (Tencent) | 活跃供应商端点数：`1` 家
- **偏好应用 (Top 2)**：1. **Hermes Agent**（流量份额 `75.8%`，累计 `851.8B` tokens） | 2. **Nous Research API**（流量份额 `10.8%`，累计 `121.1B` tokens）

#### 1.5 OpenAI: GPT-6 Luna (`openai/gpt-6-luna-20260922`)

- **总消耗 Token**：`8,395,937,696,213` (8.396T Tokens)
- **全平台消费份额占比**：`1.52%`
- **Token 输入/输出**：输入 Prompt `8,105,735,507,546` | 输出 Completion `290,202,188,667` | **I/O 比例：`27.93:1`**
- **官方标称单价**：标称输入 `$0.1000/M` | 标称输出 `$0.5000/M` | 缓存读取 `$0.0100/M`
- **供应商实际最低单价**：实际输入 `$0.0500/M` (OpenAI) | 实际输出 `$0.2500/M` (OpenAI) | 活跃供应商端点数：`7` 家
- **偏好应用 (Top 2)**：1. **Codex**（流量份额 `56.9%`，累计 `3.95T` tokens） | 2. **Hermes Agent**（流量份额 `25.0%`，累计 `1.73T` tokens）
- **优势细分场景**：`writing.summarization`

### 2. 全平台消费份额前 5 模型指标

#### 2.1 Anthropic: Claude Opus 5.5 (`anthropic/claude-opus-5.5-20260921`)

- **全平台消费份额占比**：**`14.11%`**
- **总消耗 Token**：`6,983,029,392,289` (6.983T Tokens) | 调用请求数：`64,604,698`
- **Token 输入/输出**：输入 Prompt `6,925,059,657,028` | 输出 Completion `57,969,735,261` | **I/O 比例：`119.46:1`**
- **官方标称单价**：标称输入 `$4.0000/M` | 标称输出 `$20.0000/M` | 缓存读取 `$0.2000/M`
- **供应商实际最低单价**：实际输入 `$4.0000/M` (Amazon Bedrock, Anthropic 等) | 实际输出 `$20.0000/M` (Amazon Bedrock, Anthropic 等) | 活跃供应商端点数：`11` 家
- **偏好应用 (Top 2)**：1. **Claude Code**（流量份额 `79.8%`，累计 `11.77T` tokens） | 2. **Hermes Agent**（流量份额 `8.3%`，累计 `1.23T` tokens）
- **优势细分场景**：`assistance.workflow_control`

#### 2.2 Google: Gemini 4 Carbon (`google/gemini-4-carbon-20261110`)

- **全平台消费份额占比**：**`5.92%`**
- **总消耗 Token**：`2,424,507,027,947` (2.425T Tokens) | 调用请求数：`23,988,341`
- **Token 输入/输出**：输入 Prompt `2,368,704,534,205` | 输出 Completion `55,802,493,742` | **I/O 比例：`42.45:1`**
- **官方标称单价**：标称输入 `$2.0000/M` | 标称输出 `$10.0000/M` | 缓存读取 `$0.1000/M`
- **供应商实际最低单价**：实际输入 `$1.0000/M` (Google AI Studio) | 实际输出 `$5.0000/M` (Google AI Studio) | 活跃供应商端点数：`5` 家
- **偏好应用 (Top 2)**：1. **Hermes Agent**（流量份额 `25.5%`，累计 `72.3B` tokens） | 2. **Codex**（流量份额 `24.0%`，累计 `68.0B` tokens）
- **优势细分场景**：`information.math_logic`

#### 2.3 Anthropic: Claude Sonnet 5.5 (`anthropic/claude-sonnet-5.5-20260928`)

- **全平台消费份额占比**：**`5.39%`**
- **总消耗 Token**：`2,797,804,897,264` (2.798T Tokens) | 调用请求数：`62,552,024`
- **Token 输入/输出**：输入 Prompt `2,753,470,136,875` | 输出 Completion `44,334,760,389` | **I/O 比例：`62.11:1`**
- **官方标称单价**：标称输入 `$2.0000/M` | 标称输出 `$10.0000/M` | 缓存读取 `$0.1000/M`
- **供应商实际最低单价**：实际输入 `$2.0000/M` (Amazon Bedrock, Anthropic 等) | 实际输出 `$10.0000/M` (Amazon Bedrock, Anthropic 等) | 活跃供应商端点数：`8` 家
- **偏好应用 (Top 2)**：1. **Claude Code**（流量份额 `52.8%`，累计 `2.21T` tokens） | 2. **Descript**（流量份额 `17.6%`，累计 `738.0B` tokens）
- **优势细分场景**：`assistance.casual_conversation`

#### 2.4 MoonshotAI: Kimi K3.1 Pro (`moonshotai/kimi-k3.1-pro-20261023`)

- **全平台消费份额占比**：**`4.78%`**
- **总消耗 Token**：`4,066,582,297,463` (4.067T Tokens) | 调用请求数：`40,029,524`
- **Token 输入/输出**：输入 Prompt `4,036,063,992,380` | 输出 Completion `30,518,305,083` | **I/O 比例：`132.25:1`**
- **官方标称单价**：标称输入 `$0.2403/M` | 标称输出 `$8.4023/M` | 缓存读取 `$0.2000/M`
- **供应商实际最低单价**：实际输入 `$0.1900/M` (Relace) | 实际输出 `$8.9276/M` (Relace) | 活跃供应商端点数：`23` 家
- **偏好应用 (Top 2)**：1. **Portkey AI**（流量份额 `36.7%`，累计 `705.1B` tokens） | 2. **pi**（流量份额 `20.6%`，累计 `396.2B` tokens）
- **优势细分场景**：`software.implementation`

#### 2.5 DeepSeek: DeepSeek V4.1 Flash 1017 (`deepseek/deepseek-v4.1-flash-20261017`)

- **全平台消费份额占比**：**`4.68%`**
- **总消耗 Token**：`65,077,293,847,944` (65.077T Tokens) | 调用请求数：`946,943,091`
- **Token 输入/输出**：输入 Prompt `64,164,714,565,388` | 输出 Completion `912,579,282,556` | **I/O 比例：`70.31:1`**
- **官方标称单价**：标称输入 `$0.1500/M` | 标称输出 `$0.6000/M` | 缓存读取 `$0.0030/M`
- **供应商实际最低单价**：实际输入 `$0.0200/M` (OpenInference) | 实际输出 `$0.1500/M` (Sail Research) | 活跃供应商端点数：`34` 家
- **偏好应用 (Top 2)**：1. **Hermes Agent**（流量份额 `44.2%`，累计 `8.35T` tokens） | 2. **Claude Code**（流量份额 `20.1%`，累计 `3.80T` tokens）
- **优势细分场景**：`software.security_assessment`

---

## 三、 全平台任务场景大类与小类分布全景

> [!NOTE]
> **数据统计时间窗口说明**：全平台任务场景大类与小类分布数据来源于 OpenRouter 官方细分任务开销接口（`task-spend`）。根据接口元数据定义，其统计窗口为**过去 30 天滚动消费支出（Rolling 30-Day Window，`windowDays: 30`）**，以全平台各场景所消耗的美元金额为权重统计。该统计平滑了短期偶然波动，真实反映各模型在垂直生产场景与工作流中的中长期落地渗透情况（与周度榜单的 7 天滚动用量形成互补）。

### 1. 宏观大类分布概览

| 宏观大类 | 标识 Key | 全平台支出占比 | 细分小类数量 | 核心特征 |
|:---|:---:|:---:|:---:|:---|
| **Software** | `software` | **40.34%** | 10 个 | 相关业务场景 |
| **Data 数据处理加工** | `data` | **20.85%** | 7 个 | 非结构化数据抽取、格式清洗与转换 |
| **Information** | `information` | **14.69%** | 6 个 | 相关业务场景 |
| **Writing** | `writing` | **6.80%** | 4 个 | 相关业务场景 |
| **Assistance** | `assistance` | **6.47%** | 5 个 | 相关业务场景 |
| **Creative** | `creative` | **6.32%** | 2 个 | 相关业务场景 |
| **Media** | `media` | **4.26%** | 4 个 | 相关业务场景 |
| **Retrieval** | `retrieval` | **0.28%** | 2 个 | 相关业务场景 |

### 2. 全量大类与小类明细表

#### 2.1 Software（全平台支出：40.34%）

| 细分小类标签 (`tag`) | 中文业务场景 | 全平台支出占比 | 场景领跑模型（市场份额） |
|:---|:---|:---:|:---|
| `software.implementation` | 细分专业场景 | 16.19% | Claude Opus 5.5 (22.0%) |
| `software.debugging` | 细分专业场景 | 7.34% | Claude Opus 5.5 (17.4%) |
| `software.code_review` | 细分专业场景 | 5.29% | Claude Opus 5.5 (19.5%) |
| `software.testing_verification` | 细分专业场景 | 2.98% | Claude Opus 5.5 (20.8%) |
| `software.security_assessment` | 细分专业场景 | 2.54% | DeepSeek V4.1 Flash 1017 (20.6%) |
| `software.infrastructure_devops` | 细分专业场景 | 2.04% | Claude Opus 5.5 (22.9%) |
| `software.architecture_requirements_planning` | 细分专业场景 | 1.49% | Claude Opus 5.5 (22.3%) |
| `software.code_explanation_documentation` | 细分专业场景 | 1.45% | Claude Opus 5.5 (20.8%) |
| `software.refactoring_optimization` | 细分专业场景 | 0.86% | Claude Opus 5.5 (27.4%) |
| `software.database_sql` | 细分专业场景 | 0.15% | GPT-6 Astra Pro (26.1%) |

#### 2.2 Data 数据处理类（全平台支出：20.85%）

| 细分小类标签 (`tag`) | 中文业务场景 | 全平台支出占比 | 场景领跑模型（市场份额） |
|:---|:---|:---:|:---|
| `data.classification_tagging` | 细分专业场景 | 8.89% | Claude Opus 5.5 (7.0%) |
| `data.extraction` | 细分专业场景 | 5.16% | GLM 5.3 Flash (6.2%) |
| `data.evaluation` | 细分专业场景 | 2.85% | GLM 5.3 Flash (12.2%) |
| `data.analysis` | 细分专业场景 | 2.00% | Claude Opus 5.5 (12.5%) |
| `data.transformation` | 细分专业场景 | 1.13% | GPT-6 Astra (14.3%) |
| `data.reconciliation_consolidation` | 细分专业场景 | 0.74% | Claude Opus 5.5 (13.0%) |
| `data.visualization` | 细分专业场景 | 0.08% | Claude Sonnet 4.6 (22.9%) |

#### 2.3 Information（全平台支出：14.69%）

| 细分小类标签 (`tag`) | 中文业务场景 | 全平台支出占比 | 场景领跑模型（市场份额） |
|:---|:---|:---:|:---|
| `information.context_grounded_qa` | 细分专业场景 | 6.42% | Claude Opus 5.5 (12.9%) |
| `information.research_synthesis` | 细分专业场景 | 3.24% | Claude Opus 5.5 (14.0%) |
| `information.planning_decision_support` | 细分专业场景 | 1.78% | Claude Opus 5.5 (16.6%) |
| `information.factual_qa` | 细分专业场景 | 1.44% | Claude Opus 5.5 (9.4%) |
| `information.math_logic` | 细分专业场景 | 1.11% | Gemini 4 Carbon (10.7%) |
| `information.explanation_tutoring` | 细分专业场景 | 0.71% | Claude Opus 5.5 (11.2%) |

#### 2.4 Writing（全平台支出：6.80%）

| 细分小类标签 (`tag`) | 中文业务场景 | 全平台支出占比 | 场景领跑模型（市场份额） |
|:---|:---|:---:|:---|
| `writing.drafting` | 细分专业场景 | 4.18% | Claude Opus 5.5 (14.2%) |
| `writing.rewriting_editing` | 细分专业场景 | 1.36% | Claude Opus 5.5 (16.1%) |
| `writing.summarization` | 细分专业场景 | 0.73% | Claude Opus 5.5 (8.3%) |
| `writing.translation_localization` | 细分专业场景 | 0.53% | GPT-6 Astra (8.1%) |

#### 2.5 Assistance（全平台支出：6.47%）

| 细分小类标签 (`tag`) | 中文业务场景 | 全平台支出占比 | 场景领跑模型（市场份额） |
|:---|:---|:---:|:---|
| `assistance.service_issue_resolution` | 细分专业场景 | 2.06% | Claude Opus 5.5 (12.0%) |
| `assistance.transactional_assistance` | 细分专业场景 | 1.86% | Claude Opus 5.5 (13.8%) |
| `assistance.workflow_control` | 细分专业场景 | 1.64% | Claude Opus 5.5 (32.8%) |
| `assistance.casual_conversation` | 细分专业场景 | 0.54% | Claude Opus 5.5 (11.9%) |
| `assistance.advice_coaching` | 细分专业场景 | 0.36% | Claude Opus 5.5 (11.0%) |

#### 2.6 Creative（全平台支出：6.32%）

| 细分小类标签 (`tag`) | 中文业务场景 | 全平台支出占比 | 场景领跑模型（市场份额） |
|:---|:---|:---:|:---|
| `creative.interactive_roleplay` | 细分专业场景 | 5.22% | Gemini 3.8 Flash (9.2%) |
| `creative.creative_writing` | 细分专业场景 | 1.10% | Claude Opus 5.5 (12.8%) |

#### 2.7 Media（全平台支出：4.26%）

| 细分小类标签 (`tag`) | 中文业务场景 | 全平台支出占比 | 场景领跑模型（市场份额） |
|:---|:---|:---:|:---|
| `media.image_generation_editing` | 细分专业场景 | 2.58% | Nano Banana 2 (Gemini 3.1 Flash Image) (21.8%) |
| `media.video_generation` | 细分专业场景 | 1.20% | seedance-2.5-20260807 (17.4%) |
| `media.speech_transcription` | 细分专业场景 | 0.30% | mai-transcribe-2-20260903 (19.6%) |
| `media.speech_synthesis` | 细分专业场景 | 0.18% | eleven-v4-20260930 (21.1%) |

#### 2.8 Retrieval（全平台支出：0.28%）

| 细分小类标签 (`tag`) | 中文业务场景 | 全平台支出占比 | 场景领跑模型（市场份额） |
|:---|:---|:---:|:---|
| `retrieval.embedding` | 细分专业场景 | 0.14% | GPT-5.6 Sol (16.4%) |
| `retrieval.reranking` | 细分专业场景 | 0.14% | Qwen3.8 27B (13.8%) |

---

## 四、 榜单指标与分析方法论

本报告核心指标的统计定义与计算口径如下：

**1. 物理 Token 消耗与输入输出比（Input/Output Ratio）**：
设模型在统计周期内的提示词输入 Token 为 \(N_p\)，模型生成输出 Token 为 \(N_c\)，总物理消耗 \(T = N_p + N_c\)。
输入输出比 \(r\) 反映应用的典型交互模式：
\[ r = \frac{N_p}{N_c} \]

在智能体协作、代码重构等长上下文场景中，通常呈现极高的 \(r\)（如 50:1 至 100:1 以上）。

**2. 全平台消费份额占比（Platform Spend Share）**：
数据来源于 OpenRouter 官方 7 天滚动支出排行榜接口（`GET /api/frontend/v1/rankings/models?metric=spend`）。接口返回的 `rankingMetricValue` 直接给出了过去 7 天内各模型占全平台开发者总支出的相对比例：
\[ \text{Spend Share}_i = \text{rankingMetricValue}_i \times 100\% \]

该份额直接反映模型在全平台商业变现与开发者真实付费预算层面的市场占有率。

**3. 全平台厂商消费份额聚合方法（Vendor Spend Share Methodology）**：
厂商消费份额基于模型研发/发布厂商口径（Model Creator），通过将全平台所有模型的 7 天滚动支出指标（`rankingMetricValue`）按模型命名空间（Permaslug 组织名前缀）归集累加得出：
\[ \text{Spend Share}_{\text{Vendor}} = \sum_{m \in \text{Vendor}} \text{rankingMetricValue}_m \times 100\% \]

该指标揭示了平台开发者在各基础大模型厂商之间的真实付费预算分配与商业生态格局。

**4. 首选偏好应用流量份额（Top Apps Traffic Share）**：
OpenRouter 官方模型详情页中的 Top Apps 展示了各客户端自接入以来的全量累计消耗。为消除绝对累计量与 7 天统计周期之间的量纲差异，报告取前序主要应用的流量比重计算相对偏好份额：
\[ \text{Share}_i = \frac{\text{Tokens}_i}{\sum_{k \in \text{Top Apps}} \text{Tokens}_k} \times 100\% \]

**5. 优势细分场景与场景分布统计口径（Task Scenario Methodology）**：
- **数据源与接口**：来自 OpenRouter 官方细分任务支出接口（`GET /api/frontend/v1/rankings/task-spend`）。
- **统计时间窗口**：根据官方接口返回的 `windowDays: 30` 字段，统计基于**过去 30 天滚动窗口（Rolling 30-Day Window）**的全平台美元消费支出（Spend Share），而非 Token 数量。
- **指标作用与互补性**：核心榜单聚焦 7 天滚动用量以捕捉实时流量爆发；任务场景分布采用 30 天统计窗口以平滑短期偶然波动，揭示各模型在垂直领域生产环境与智能体流程中的中长期商业渗透与核心优势壁垒。各模型详细指标中的“优势细分场景”为该模型在过去 30 天内取得市场份额第一（Top 1）的细分任务标签（若无公开细分数据则不展示）。

**6. 模型标称单价与供应商实际最低单价统计口径（Pricing Methodology）**：
- **输入输出合并呈现口径**：榜单表格中采用 `输入单价 / 输出单价`（入/出）合并格式呈现，计量单位统一为美元每百万 Token（`$/M`）。
- **官方标称单价（Nominal Price）**：来源于 OpenRouter 官方模型元数据目录接口（`GET /api/v1/models`），为模型开发者或官方维护的标准参考基准定价。
- **供应商实际单价（Actual Provider Lowest Price）**：
  - 数据接口：来源于 OpenRouter 官方模型底层端点明细接口（`GET /api/v1/models/{model_id}/endpoints`）。
  - 统计逻辑：遍历该模型接入的所有底层推理供应商（如官方直连、第三方云服务商、托管推理集群等），过滤服务状态为活跃（`status == 0`）的端点，分别取所有可用供应商中的最低提示词输入单价（Min Prompt Price）与最低生成输出单价（Min Completion Price）：
    \[ P_{\text{actual, in}} = \min_{e \in \text{Active Endpoints}} P_{\text{prompt}}(e) \]
    \[ P_{\text{actual, out}} = \min_{e \in \text{Active Endpoints}} P_{\text{completion}}(e) \]
  - 现实意义：OpenRouter 采用多供应商路由机制，开发者可通过指定供应商优先级或特定通道获取显著低于标称价的底价算力（如输入单价折扣高达 68%）。该指标客观揭示了模型在生产部署中的供给侧极限底价与套利/降本空间。

