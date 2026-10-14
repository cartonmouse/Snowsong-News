# News Agent

每日 AI 新闻助手 Agent，依据用户身份和订阅偏好整理个性化新闻简报。

## 当前状态

当前已完成项目骨架、五个题目要求的基础工具、动态 Function Calling Agent、RSS/Mock 新闻源、SQLite 数据库、简报交付工具和基础网页界面。定时任务、生产级配置和最终演示文档将在后续阶段补齐。

## 快速启动

建议使用 Python 3.11 或更高版本。

在项目根目录执行：

    python -m venv .venv
    .venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt
    Copy-Item .env.example .env
    python -m uvicorn app.main:app --reload

启动后访问：

- 健康检查：http://127.0.0.1:8000/health
- API 文档：http://127.0.0.1:8000/docs
- 新闻助手页面：http://127.0.0.1:8000/

## 测试

    python -m pytest

## 本地演示

1. 打开新闻助手页面。
2. 输入姓名和身份。
3. 设置关注话题和关键词。
4. 点击保存偏好。
5. 点击立即生成简报。
6. 查看简报内容、历史记录和 Agent 工具调用轨迹。

默认配置使用 Mock LLM 和 Mock 新闻源，不需要 API Key 即可完成本地演示。

## 主要 API

- POST /api/users：创建或更新用户。
- PUT /api/users/{user_id}/subscription：保存订阅偏好。
- GET /api/users/{user_id}/preferences：读取订阅偏好。
- POST /api/users/{user_id}/generate：运行一次新闻 Agent。
- GET /api/users/{user_id}/briefs：查看历史简报。

## 配置原则

- 敏感配置只通过环境变量或本地 .env 提供。
- .env 不提交到 Git。
- 没有真实 LLM 配置时，项目优先使用 mock 模式进行本地开发和测试。

## 目录规划

    app/          应用代码
    migrations/   数据库迁移脚本
    data/         本地运行数据
    tests/        自动化测试

## 题目要求

本项目对应跨赴笔试中的“每日 AI 新闻助手 Agent”题目，核心要求是由 LLM 决定工具调用顺序，而不是由代码硬编码固定线性流程。

