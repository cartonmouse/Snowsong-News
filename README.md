<div align="center">

<img src="assets/news-agent-icon.png" alt="News Agent 项目图标" width="180" />

# News Agent

**一个会主动调用工具、聚合真实新闻源并生成个性化简报的 AI 新闻助手。**

支持中文订阅偏好匹配英文新闻，使用 RSS/Atom 获取国内外新闻，并通过 Mock LLM 或 DeepSeek 等 OpenAI-compatible LLM 驱动 Agent。

<p>
  <a href="docs/ARCHITECTURE.md">架构说明</a> ·
  <a href="docs/NEWS_SOURCES.md">新闻源说明</a>
</p>

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)
![RSS](https://img.shields.io/badge/News%20source-RSS%20%2F%20Atom-FF8C42.svg)
![Agent](https://img.shields.io/badge/Agent-Function%20Calling-6E56CF.svg)
![Database](https://img.shields.io/badge/Database-SQLite-003B57.svg)

</div>

## 这是什么

很多新闻工具只能展示固定的信息流，用户需要自己翻阅、筛选和整理。News Agent 的目标是把这条链路交给 Agent：用户只需要告诉它自己的身份、关注话题和关键词，系统就会从配置的新闻源中获取内容，筛选相关报道，生成简报并保存到历史记录。

这个项目是一个面向笔试题的可运行实现，也可以作为轻量级 AI Agent、RSS 聚合和 Function Calling 的学习样例。

## 功能闭环

| 环节 | 能力 |
| --- | --- |
| 用户画像 | 填写姓名、身份和订阅偏好 |
| 中文订阅 | 输入中文主题，匹配英文新闻表达 |
| 新闻获取 | 并发读取国内外 RSS/Atom 新闻源 |
| Agent 决策 | LLM 自主选择工具、调用次数和结束时机 |
| 简报生成 | 汇总标题、摘要、来源和原文链接 |
| 历史记录 | 将简报、运行状态和工具轨迹写入 SQLite |
| 交付 | 默认保存到网页历史，可选 Webhook |
| 自动化 | 支持 APScheduler 每日定时运行 |

### 中文输入也能匹配英文新闻

客户可以直接输入中文，不需要先把所有关键词翻译成英文：

| 中文输入 | 内置英文扩展 |
| --- | --- |
| 大语言模型 | `LLM`、`large language model`、`foundation model` |
| 人工智能 | `AI`、`artificial intelligence` |
| 智能体 | `AI agent`、`agentic AI`、`agents` |
| 函数调用 | `function calling`、`tool calling`、`tool use` |
| 检索增强生成 | `RAG`、`retrieval augmented generation` |
| 多模态 | `multimodal`、`vision-language` |
| 芯片 | `chip`、`semiconductor`、`GPU` |
| 科技股票 | `AI stocks`、`tech stocks`、`stock market`、`earnings` |

网页支持英文逗号、中文逗号、顿号和换行作为分隔符，例如：

```text
大语言模型、RAG、DeepSeek、科技股票
```

## 5 分钟启动

### 环境要求

- Python 3.11 或更高版本
- 能够访问 RSS/Atom 新闻源的网络环境
- 使用真实 LLM 时，需要对应服务的 API Key

### 安装

在项目根目录执行：

```powershell
python -m venv .venv
./.venv/Scripts/Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

### 启动

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

启动成功后访问：

- 新闻助手页面：<http://127.0.0.1:8000/>
- 健康检查：<http://127.0.0.1:8000/health>
- API 文档：<http://127.0.0.1:8000/docs>

如果 8000 端口被占用，可以使用 8001：

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

此时浏览器也必须访问 <http://127.0.0.1:8001/>。项目路径包含特殊字符时，建议使用：

```powershell
Set-Location -LiteralPath "D:/3BUPT/mark'workshop/news-agent"
```

## 默认配置与真实新闻源

程序在 `app/news/defaults.py` 中内置了 16 个国内外 RSS/Atom 来源。客户不需要重新填写 `NEWS_FEEDS`，默认配置相当于：

```dotenv
NEWS_MODE=rss
NEWS_FALLBACK_TO_MOCK=false
```

当前来源包括：

- 国际：OpenAI、Google、Hugging Face、TechCrunch AI、The Verge、MIT Technology Review、NVIDIA、Microsoft Research、Bloomberg、Investing.com 等；
- 国内：InfoQ 中文、极客公园、IT之家，以及公开 RSS 镜像来源。

### 自定义新闻源

如果需要替换或增加来源，可以在 `.env` 中配置 `NEWS_FEEDS`。多个地址使用英文逗号分隔：

```dotenv
NEWS_FEEDS=https://example.com/feed.xml,https://example.com/atom.xml
```

注意：配置 `NEWS_FEEDS` 后会覆盖内置列表，而不是追加到内置列表。RSS 请求失败时，单个来源不会阻断其他来源；只有全部来源失败时才会返回整体错误。客户环境建议保持 `NEWS_FALLBACK_TO_MOCK=false`，避免把演示数据误认为真实新闻。

完整来源列表、故障字段和匹配逻辑见 [`docs/NEWS_SOURCES.md`](docs/NEWS_SOURCES.md)。

## LLM 配置

### 默认 Mock LLM

默认 `.env.example` 使用 `LLM_MODEL=mock`。这种模式不需要 API Key，可以完成完整的本地演示；新闻内容仍可来自真实 RSS。

### DeepSeek

如果希望由真实 LLM 驱动 Agent，在 `.env` 中填写：

```dotenv
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_API_KEY=your-deepseek-api-key
LLM_MODEL=your-available-deepseek-model
```

`OPENAI_BASE_URL` 填服务根地址，程序会请求其 `/chat/completions` 接口。API Key 只保存在本地 `.env`，不要提交到 Git、写入 README 或发送到聊天中。

项目也支持其他 OpenAI-compatible 服务：

```dotenv
OPENAI_BASE_URL=https://your-provider.example/v1
OPENAI_API_KEY=your-key
LLM_MODEL=your-model
```

如果真实 LLM 三项配置不完整，当前工厂会回退到本地 `DemoNewsProvider`，方便演示；生产环境排查时应确认模型名、Base URL 和 Key 已生效。

## Agent 如何工作

核心约束是：工具调用顺序由 LLM 决定，而不是由业务代码写死。

```text
用户请求
   │
   ▼
LLM + 工具 Schema
   │
   ├── 返回最终答案 ───────────────┐
   │                              │
   └── 返回一个或多个 tool_calls    │
          │                       │
          ▼                       │
      ToolRegistry                │
          │                       │
          ▼                       │
      工具执行结果 ──回到消息上下文─┘
```

每一轮 Agent 都会把当前消息和工具 Schema 交给 LLM。LLM 可以自主决定先读取偏好、先获取新闻、重复调用工具，或者直接结束。`MAX_AGENT_STEPS` 用于限制最大循环次数，避免无限调用。

### 题目要求的通用工具

| 工具 | 实现位置 | 作用 |
| --- | --- | --- |
| `list_dir(path)` | `app/tools/filesystem.py` | 列出工作区目录 |
| `read_file(path)` | `app/tools/filesystem.py` | 读取工作区文件 |
| `search_content(keyword, dir)` | `app/tools/filesystem.py` | 按关键词搜索文件内容 |
| `write_file(path, content)` | `app/tools/filesystem.py` | 写入工作区文件 |
| `bash(command)` | `app/tools/shell.py` | 执行受限制的 Shell 命令 |

文件工具限制在 `data/agent_workspace` 内；Shell 工具限制可执行程序、危险命令、工作目录、超时时间和输出长度。

### 新闻业务工具

| 工具 | 作用 |
| --- | --- |
| `get_user_preferences` | 读取用户身份和订阅偏好 |
| `fetch_news` | 获取并筛选 RSS/Mock 新闻 |
| `save_brief` | 保存新闻简报 |
| `deliver_brief` | 交付到历史记录或 Webhook |

## 技术架构

```text
浏览器
  │
  ▼
FastAPI API
  │
  ▼
共享新闻生成服务
  │
  ├─ NewsRepository       用户、订阅、简报和运行记录
  ├─ NewsService          RSS/Mock 来源与关键词筛选
  ├─ LLM Provider         Mock 或 OpenAI-compatible 服务
  ├─ ToolRegistry         工具 Schema 和动态分发
  └─ AgentRunner          Function Calling 循环
```

| 层 | 技术与职责 |
| --- | --- |
| Web | FastAPI、Uvicorn、原生 HTML/CSS/JavaScript |
| Agent | 手写 Function Calling / ReAct 风格循环 |
| Provider | Mock Provider、OpenAI-compatible Provider |
| News | RSS 2.0、Atom、并发抓取、中文同义词扩展 |
| Storage | SQLite、SQLAlchemy、Repository |
| Scheduler | APScheduler Cron，支持时区配置 |
| Delivery | 历史记录、可选 Webhook |
| Tests | pytest，覆盖 API、Agent、工具、数据库、RSS 和调度 |

## 项目目录

```text
news-agent/
├─ app/
│  ├─ agent/          Agent Runner、Mock Provider、LLM Provider
│  ├─ api/            FastAPI 路由与请求模型
│  ├─ core/           环境变量配置
│  ├─ news/           RSS 读取、默认来源、解析和新闻匹配
│  ├─ services/       手动生成和定时生成共用的业务入口
│  ├─ storage/        SQLite 数据库、模型和 Repository
│  ├─ tools/          通用工具与新闻业务工具
│  ├─ scheduler.py    每日调度器
│  ├─ main.py         FastAPI 应用入口
│  └─ web/            简单前端页面
├─ assets/             README 项目图标
├─ migrations/         数据库迁移脚本
├─ tests/              自动化测试
├─ docs/               架构、演示、面试和新闻源说明
├─ data/               SQLite 数据库和 Agent 工作区
├─ .env.example        环境变量模板
└─ requirements.txt    Python 依赖
```

## 数据与持久化

默认数据库为 `data/news_agent.db`，启动时会执行 `migrations/001_initial.sql`。

| 表 | 保存内容 |
| --- | --- |
| `users` | 用户姓名和身份 |
| `subscriptions` | 话题、关键词、来源和交付渠道 |
| `briefs` | 已保存的新闻简报 |
| `agent_runs` | Agent 运行状态、步数和错误 |
| `tool_calls` | 工具调用参数摘要、结果摘要和耗时 |

删除数据库会丢失本地用户、订阅、简报和运行记录；备份前请停止服务或复制到单独位置。

## API

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| `GET` | `/health` | 健康检查 |
| `POST` | `/api/users` | 创建或更新用户 |
| `PUT` | `/api/users/{user_id}/subscription` | 保存订阅偏好 |
| `GET` | `/api/users/{user_id}/preferences` | 获取订阅偏好 |
| `POST` | `/api/users/{user_id}/generate` | 运行一次新闻 Agent |
| `GET` | `/api/users/{user_id}/briefs` | 获取历史简报 |
| `GET` | `/docs` | FastAPI 自动 API 文档 |

## 每日调度

调度器默认关闭。需要每天自动生成时，在 `.env` 中配置：

```dotenv
SCHEDULER_ENABLED=true
SCHEDULE_HOUR=8
SCHEDULE_MINUTE=0
SCHEDULE_TIMEZONE=Asia/Shanghai
```

定时任务会遍历已经保存的用户，并调用与网页手动生成相同的新闻生成服务。

## 测试与质量检查

运行测试：

```powershell
python -m pytest
```

当前版本测试覆盖 Agent 动态工具顺序、工具异常、最大步数、API 端到端流程、RSS 解析、中文关键词扩展、部分新闻源失败、数据库、Shell 安全限制和调度器。

## 题目要求映射

| 题目要求 | 本项目实现 |
| --- | --- |
| Python | FastAPI + Python 3.11+ |
| 至少 5 个工具 | `list_dir`、`read_file`、`search_content`、`write_file`、`bash` |
| 工具顺序由 LLM 决定 | `AgentRunner` 根据 `tool_calls` 动态循环，不写死线性流程 |
| 用户订阅偏好 | 网页填写身份、话题和关键词，保存到 SQLite |
| 简单前端 | `app/web/index.html` 提供保存、生成、历史和轨迹查看 |
| 新闻来源 | RSS/Atom 多源读取，内置国内外来源 |
| 个性化简报 | 关键词筛选后生成标题、摘要、来源和链接 |
| Git 版本管理 | 保留完整提交历史，提交说明使用中文 |
| 密钥不硬编码 | `.env` 环境变量，`.env` 不提交 Git |
| 依赖清单 | `requirements.txt` |
| 数据库建表脚本 | `migrations/001_initial.sql` |
| 可运行交付 | FastAPI 服务、网页、API、测试和运行文档 |

## 常见问题

### 页面显示“今天没有匹配到新闻”

这可能是关键词没有命中，而不一定是 RSS 失败。先尝试 `AI、人工智能、大语言模型`，再查看网页中的 Agent 工具调用轨迹，确认 `successful_feeds` 和 `feed_errors`。

### 出现 `401 Authorization Required`

说明后端已经请求 LLM，但 API Key 未通过认证。检查 `OPENAI_BASE_URL`、`OPENAI_API_KEY` 和 `LLM_MODEL`，并确认修改 `.env` 后已经重启后端。不要把完整 API Key 发给他人。

### 出现 `WinError 10048`

说明 8000 端口已被占用。可以停止属于本项目的旧 Uvicorn 进程，或改用 8001。使用 `--reload` 时可能存在父子进程，结束进程前应先确认进程归属。

### 修改 `.env` 后页面没有变化

`.env` 在后端启动时读取。修改后请按 `Ctrl+C` 停止服务，再重新执行启动命令；只刷新网页不会重载后端配置。

## 文档

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)：系统分层、Agent 循环和失败处理。
- [`docs/NEWS_SOURCES.md`](docs/NEWS_SOURCES.md)：内置 RSS 来源、中文检索和来源排障。
- [`docs/DEMO.md`](docs/DEMO.md)：3 分钟演示脚本。
- [`docs/INTERVIEW.md`](docs/INTERVIEW.md)：面试问题准备。

## 安全边界与已知限制

- `.env` 中的 API Key 不应提交、截图或写入文档；
- RSS 内容来自第三方站点，使用者应打开原文核验重要信息；
- SQLite 适合本地演示和小规模使用，生产环境需要评估更强的数据库；
- RSS 来源可能因网络、403、频率限制或地址变更而失效；
- 当前未提供用户登录认证，公开部署前需要补充认证、HTTPS、限流和日志脱敏；
- 当前未提供完整的新闻去重、缓存和发布时间排序策略；
- 默认的 LLM 配置不完整时会回退到 Mock Provider，生产环境建议改为显式配置检查。

## License

当前仓库未单独声明开源许可证。如需公开分发，请根据部署和使用场景补充合适的 LICENSE 文件。

