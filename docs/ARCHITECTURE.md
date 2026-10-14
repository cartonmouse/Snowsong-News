# News Agent 架构说明

## 1. 系统分层

用户浏览器
→ FastAPI API 和简单网页
→ 共享新闻生成服务
→ AgentRunner
→ LLM Provider
→ ToolRegistry
→ 文件工具、新闻工具、数据库和推送工具

定时调度器和手动生成 API 都调用同一个共享新闻生成服务，因此不会因为触发方式不同而产生两套业务流程。

## 2. 动态 Agent 循环

AgentRunner 不预设搜索、读取、保存和推送的固定顺序。每轮执行过程是：

1. 向 LLM 提供当前消息、用户请求和工具 schema。
2. LLM 返回最终答案或一个或多个工具调用。
3. ToolRegistry 根据工具名称分发调用。
4. 工具结果以 tool message 形式加入上下文。
5. 再次调用 LLM。
6. LLM 输出最终答案或达到最大步数后停止。

AgentRunner 会记录每次工具调用的步骤、工具名、参数摘要、结果、状态和耗时。

## 3. 工具集合

题目要求的五个工具：

- list_dir
- read_file
- search_content
- write_file
- bash

新闻业务工具：

- get_user_preferences
- fetch_news
- save_brief
- deliver_brief

文件工具限制在 data/agent_workspace 内。bash 工具限制可执行程序、禁止危险命令和 Shell 链式操作，并设置超时和输出上限。

## 4. 新闻来源

NewsService 支持两种模式：

- mock：本地确定性数据，适合测试、演示和无网络环境。
- rss：读取配置的 RSS 地址，解析 RSS 2.0 或 Atom 内容。

RSS 请求失败时回退到 Mock 数据，保证基础流程能够运行。

## 5. 数据库

数据库使用 SQLite，表结构由 migrations/001_initial.sql 初始化：

- users
- subscriptions
- briefs
- agent_runs
- tool_calls

简报和 Agent 运行轨迹分开保存，便于前端展示历史内容和面试时说明 Agent 行为。

## 6. 失败处理

- LLM 请求失败：Agent 返回 failed 状态和错误信息。
- 工具参数错误：错误结果回传给 LLM，允许模型决定下一步。
- Agent 超过最大步数：返回 max_steps 状态。
- RSS 请求失败：根据 `NEWS_FALLBACK_TO_MOCK` 配置决定是否回退到 Mock 新闻源；客户环境默认关闭回退，避免把演示内容误认为真实新闻。
- Webhook 未配置或发送失败：记录失败，不影响历史简报保存。
- 定时任务单用户失败：记录该用户失败，继续处理其他用户。

