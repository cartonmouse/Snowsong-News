# 新闻源与中文检索说明

## 当前配置

项目默认使用真实 RSS/Atom 新闻源。默认地址内置在 `app/news/defaults.py`，因此客户不配置 `.env` 也可以获取真实新闻；`.env` 中的 `NEWS_FEEDS` 只用于覆盖默认列表。
每个地址用英文逗号分隔。单个新闻源超时、返回 403 或 XML 格式异常时，会记录在 `feed_errors`，不会阻断其他新闻源；只有全部新闻源失败时，才会返回错误。当前 `NEWS_FALLBACK_TO_MOCK=false`，因此不会用演示数据冒充真实新闻。

## 国际新闻源

- OpenAI News：`https://openai.com/news/rss.xml`
- Google Blog：`https://blog.google/rss/`
- Hugging Face Blog：`https://huggingface.co/blog/feed.xml`
- TechCrunch AI：`https://techcrunch.com/category/artificial-intelligence/feed/`
- The Verge：`https://www.theverge.com/rss/index.xml`
- MIT Technology Review：`https://www.technologyreview.com/feed/`
- NVIDIA Developer Blog：`https://developer.nvidia.com/blog/feed/`
- Google Developers Blog：`https://developers.googleblog.com/feeds/posts/default`
- Microsoft Research：`https://www.microsoft.com/en-us/research/feed/`
- Bloomberg Markets：`https://feeds.bloomberg.com/markets/news.rss`
- Bloomberg Technology：`https://feeds.bloomberg.com/technology/news.rss`
- Investing.com News：`https://www.investing.com/rss/news.rss`

## 国内新闻源

- InfoQ 中文：`https://www.infoq.cn/feed.xml`
- 极客公园：`https://www.geekpark.net/rss`
- IT之家：`https://www.ithome.com/rss/`
- 机器之心 RSS 镜像：`https://feedmaker.kindle4rss.com/feeds/almosthuman2014.weixin.xml`

机器之心地址是公开 RSS 镜像，不是机器之心主站域名；如果后续失效，可以从 `NEWS_FEEDS` 删除，不影响其他来源。

## 中文关键词匹配英文新闻

新闻筛选器内置了常用中英同义词扩展，不需要客户改成英文关键词。例如：

| 中文输入 | 可匹配的英文表达 |
| --- | --- |
| 大语言模型 | LLM、large language model、foundation model |
| 智能体 | AI agent、agentic AI、agents |
| 函数调用 | function calling、tool calling、tool use |
| 检索增强生成 | RAG、retrieval augmented generation |
| 多模态 | multimodal、vision-language |
| 科技股票 | AI stocks、tech stocks、semiconductor stocks |

关键词仍支持英文逗号、中文逗号、顿号和换行分隔。

## 运维建议

1. 默认启动即使用 `NEWS_MODE=rss`；只有离线演示时才改为 `mock`。
2. 客户环境建议保留 `NEWS_FALLBACK_TO_MOCK=false`，这样 RSS 故障会明确显示，而不会产生误导内容。
3. 如果某个来源长期失败，查看 `fetch_news` 返回的 `feed_errors`，再通过 `.env` 覆盖 `NEWS_FEEDS`。
4. 新增来源前先确认返回的是 RSS/Atom XML，而不是普通网页；可以用项目现有的 `parse_feed` 做验证。
