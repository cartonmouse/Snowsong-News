"""Built-in defaults for public news sources."""

from __future__ import annotations


DEFAULT_NEWS_FEEDS: tuple[str, ...] = (
    "https://openai.com/news/rss.xml",
    "https://blog.google/rss/",
    "https://huggingface.co/blog/feed.xml",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.technologyreview.com/feed/",
    "https://developer.nvidia.com/blog/feed/",
    "https://developers.googleblog.com/feeds/posts/default",
    "https://www.microsoft.com/en-us/research/feed/",
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://feeds.bloomberg.com/technology/news.rss",
    "https://www.investing.com/rss/news.rss",
    "https://www.infoq.cn/feed.xml",
    "https://www.geekpark.net/rss",
    "https://www.ithome.com/rss/",
    "https://feedmaker.kindle4rss.com/feeds/almosthuman2014.weixin.xml",
)

DEFAULT_NEWS_FEEDS_VALUE = ",".join(DEFAULT_NEWS_FEEDS)
