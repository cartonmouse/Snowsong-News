<div align="center">

<img src="assets/news-agent-icon.png" alt="News Agent 项目图标" width="180" />

# Snowsong-News Agent

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

#### **输入你想看的新闻主题，Agent帮你搜集并展示**

## 功能闭环

| 环节 | 能力 |
| --- | --- |
| 用户画像 | 填写姓名、身份和订阅偏好 |
| 新闻获取 | 并发读取国内外 RSS/Atom 新闻源 |
| Agent 决策 | LLM 自主选择工具、调用次数和结束时机 |
| 简报生成 | 汇总标题、摘要、来源和原文链接 |
| 历史记录 | 将简报、运行状态和工具轨迹写入 SQLite |
| 交付 | 默认保存到网页历史，可选 Webhook |



## 5 分钟启动

### 获取项目

```powershell
git clone https://github.com/cartonmouse/Snowsong-News.git .
```

普通 `git clone` 会同时获取仓库的 Git 提交历史。

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

## 文档

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)：系统分层、Agent 循环和失败处理。
- [`docs/NEWS_SOURCES.md`](docs/NEWS_SOURCES.md)：内置 RSS 来源、中文检索和来源排障。

