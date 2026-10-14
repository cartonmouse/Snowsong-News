# News Agent

每日 AI 新闻助手 Agent，依据用户身份和订阅偏好整理个性化新闻简报。

## 当前状态

当前已完成项目骨架、五个题目要求的基础工具、动态 Function Calling Agent、RSS/Mock 新闻源、SQLite 数据库、简报交付工具、基础网页界面和每日调度。架构说明与演示脚本位于 docs 目录。

## 快速启动

建议使用 Python 3.11 或更高版本。

在项目根目录执行：

    python -m venv .venv
    .venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt
    Copy-Item .env.example .env
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

启动后访问：

- 健康检查：http://127.0.0.1:8000/health
- API 文档：http://127.0.0.1:8000/docs
- 新闻助手页面：http://127.0.0.1:8000/

如果 8000 端口已经被占用，可以改用 8001：

    python -m uvicorn app.main:app --host 127.0.0.1 --port 8001

此时浏览器也要访问 `http://127.0.0.1:8001/`。修改 `.env` 后必须重启后端，单纯刷新网页不会重新加载配置。

## 测试

    python -m pytest

## 本地演示

1. 打开新闻助手页面。
2. 输入姓名和身份。
3. 设置关注话题和关键词。
4. 点击保存偏好。
5. 点击立即生成简报。
6. 查看简报内容、历史记录和 Agent 工具调用轨迹。

默认配置使用 Mock LLM 和内置真实 RSS 新闻源，不需要 API Key 即可运行新闻获取流程，但需要网络连接。若要进行完全离线、可重复的演示，可在 `.env` 中将 `NEWS_MODE` 改为 `mock`。

## 主要 API

- POST /api/users：创建或更新用户。
- PUT /api/users/{user_id}/subscription：保存订阅偏好。
- GET /api/users/{user_id}/preferences：读取订阅偏好。
- POST /api/users/{user_id}/generate：运行一次新闻 Agent。
- GET /api/users/{user_id}/briefs：查看历史简报。

## 配置原则

- 敏感配置只通过环境变量或本地 .env 提供。
- .env 不提交到 Git。
- 默认使用真实 RSS 新闻源；没有真实 LLM 配置时，Agent 使用本地 Mock LLM，仍然可以读取真实 RSS 新闻。
- 应用启动时会执行 migrations/001_initial.sql，初始化所需数据库表。

## 默认新闻源

程序在 `app/news/defaults.py` 中内置了 16 个国内外 RSS/Atom 新闻源。客户不需要重新填写新闻源地址，应用启动后默认使用：

    NEWS_MODE=rss
    NEWS_FALLBACK_TO_MOCK=false

RSS 新闻获取需要网络连接。单个来源失败不会阻断其他来源；如果全部来源失败，系统会返回明确错误，而不会把 Mock 数据误认为真实新闻。

如需替换或增加来源，可在 `.env` 中覆盖 `NEWS_FEEDS`。多个地址用英文逗号分隔：

    NEWS_FEEDS=https://example.com/feed.xml

配置 `NEWS_FEEDS` 后会覆盖内置列表，而不是追加到内置列表。完整来源和中文关键词匹配说明见 `docs/NEWS_SOURCES.md`。

## 配置真实 LLM

没有真实 LLM 配置时，系统使用 Mock LLM；如果希望由真实 LLM 驱动 Agent，需要在 `.env` 中配置 OpenAI-compatible 服务：

若要使用真实 OpenAI-compatible LLM，可在 .env 中设置：

    OPENAI_BASE_URL=https://your-provider.example/v1
    OPENAI_API_KEY=your-key
    LLM_MODEL=your-model

DeepSeek 配置示例：

    OPENAI_BASE_URL=https://api.deepseek.com
    OPENAI_API_KEY=your-deepseek-api-key
    LLM_MODEL=your-available-deepseek-model

API Key 只保存在本地 `.env`，不要提交到 Git、写入文档或发送到聊天中。`LLM_MODEL` 必须填写当前服务账号可用的模型名；如果配置错误，生成接口会返回 LLM 请求错误。

若要启用每日调度，可设置：

    SCHEDULER_ENABLED=true
    SCHEDULE_HOUR=8
    SCHEDULE_MINUTE=0
    SCHEDULE_TIMEZONE=Asia/Shanghai

调度器默认关闭，手动生成接口始终可用。



## 目录规划

    app/          应用代码
    migrations/   数据库迁移脚本
    data/         本地运行数据
    tests/        自动化测试
    docs/         架构、演示和面试说明


## 详细文档

- docs/ARCHITECTURE.md：系统结构和关键设计。
- docs/DEMO.md：3 分钟演示脚本。
- docs/INTERVIEW.md：面试问题准备。
- docs/NEWS_SOURCES.md：内置新闻源、RSS 故障处理和中文关键词匹配。

