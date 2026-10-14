# 3 分钟演示脚本

## 演示前准备

1. 在项目根目录安装依赖。
2. 复制 .env.example 为 .env。
3. 保持默认的 Mock LLM 和 Mock 新闻源。
4. 启动服务：

    python -m uvicorn app.main:app --reload

## 演示流程

### 0:00～0:20：介绍目标

说明这是一个每日 AI 新闻助手，用户可以填写身份和订阅偏好，Agent 会根据偏好生成新闻简报。

### 0:20～0:50：填写用户偏好

打开 http://127.0.0.1:8000/，填写：

- 姓名：Alice
- 身份：AI engineer
- 关注话题：agents
- 关键词：function calling

点击保存偏好。

### 0:50～1:50：运行 Agent

点击立即生成简报，展示：

1. 页面显示 Agent 正在工作。
2. Agent 首先读取用户偏好。
3. Agent 获取匹配新闻。
4. Agent 保存简报。
5. Agent 执行 history 渠道交付。
6. Agent 返回最终简报。

重点指出：这些步骤由 Mock Provider 模拟 LLM 的工具调用返回，生产模式下由真实 LLM 返回工具调用，AgentRunner 本身不写死业务顺序。

### 1:50～2:20：查看结果

展示：

- 本次简报；
- 新闻来源和摘要；
- Agent 工具调用轨迹；
- 调用步骤和耗时。

### 2:20～2:40：查看历史

刷新或滚动到历史简报区域，展示简报已经保存到 SQLite，并可以再次查询。

### 2:40～3:00：展示工程交付

展示：

- README；
- requirements.txt；
- migrations/001_initial.sql；
- tests；
- Git 提交历史；
- docs/ARCHITECTURE.md。

最后强调：项目支持真实 LLM、RSS 和每日调度，但默认 Mock 模式可以无密钥完成演示。

