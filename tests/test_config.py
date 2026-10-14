from app.core.config import Settings
from app.news.defaults import DEFAULT_NEWS_FEEDS


def test_settings_have_real_rss_defaults_without_env_file() -> None:
    settings = Settings(_env_file=None)

    assert settings.news_mode == "rss"
    assert settings.news_feeds.split(",") == list(DEFAULT_NEWS_FEEDS)
    assert settings.news_fallback_to_mock is False


def test_environment_values_can_override_built_in_rss_defaults() -> None:
    settings = Settings(
        _env_file=None,
        news_mode="mock",
        news_feeds="https://example.com/custom.xml",
    )

    assert settings.news_mode == "mock"
    assert settings.news_feeds == "https://example.com/custom.xml"
