# News Agent

每日 AI 新闻助手 Agent，依据用户身份和订阅偏好整理个性化新闻简报。

## 当前状态

当前完成项目骨架和健康检查接口，后续将逐步实现工具层、动态 Agent、新闻来源、前端、数据库和定时任务。

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

## 测试

    python -m pytest

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

