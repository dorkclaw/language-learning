"""
Unit tests for rss.py — no API keys needed, tests RSS parsing logic.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from src.bbc_noticias.rss import parse_rss_datetime, fetch_stories


class TestParseRssDatetime:
    def test_parses_rfc822_format(self):
        result = parse_rss_datetime("Fri, 08 May 2026 12:00:00 GMT")
        assert result is not None
        assert result.year == 2026
        assert result.month == 5
        assert result.day == 8

    def test_parses_rfc822_no_timezone(self):
        result = parse_rss_datetime("Sat, 02 Jan 2026 09:30:00 +0000")
        assert result is not None
        assert result.year == 2026

    def test_handles_none(self):
        assert parse_rss_datetime(None) is None

    def test_handles_empty_string(self):
        assert parse_rss_datetime("") is None


class TestFetchStories:
    @patch("src.bbc_noticias.rss.requests.get")
    def test_fetches_and_parses_rss(self, mock_get):
        mock_get.return_value.__enter__.return_value.status_code = 200
        mock_get.return_value.__enter__.return_value.content = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>BBC Mundo</title>
    <item>
      <title>Test Story Title</title>
      <link>https://www.bbc.com/test-story</link>
      <description>A test story description</description>
      <pubDate>Fri, 08 May 2026 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""

        stories = fetch_stories(max_age_hours=24)
        assert len(stories) == 1
        assert stories[0]["title"] == "Test Story Title"
        assert stories[0]["link"] == "https://www.bbc.com/test-story"
        assert stories[0]["source"] == "BBC Mundo"

    @patch("src.bbc_noticias.rss.requests.get")
    def test_filters_stories_older_than_max_age(self, mock_get):
        old_date = (datetime.now(timezone.utc) - timedelta(hours=30)).strftime("%a, %d %b %Y %H:%M:%S GMT")
        mock_get.return_value.__enter__.return_value.status_code = 200
        mock_get.return_value.__enter__.return_value.content = f"""<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>BBC Mundo</title>
    <item>
      <title>Old Story</title>
      <link>https://www.bbc.com/old</link>
      <description>Old story</description>
      <pubDate>{old_date}</pubDate>
    </item>
  </channel>
</rss>"""

        stories = fetch_stories(max_age_hours=24)
        assert len(stories) == 0

    @patch("src.bbc_noticias.rss.requests.get")
    def test_skips_items_without_title_or_link(self, mock_get):
        mock_get.return_value.__enter__.return_value.status_code = 200
        mock_get.return_value.__enter__.return_value.content = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>BBC Mundo</title>
    <item>
      <title>Good Story</title>
      <link>https://www.bbc.com/good</link>
      <description>Desc</description>
      <pubDate>Fri, 08 May 2026 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title></title>
      <link></link>
      <pubDate>Fri, 08 May 2026 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""

        stories = fetch_stories(max_age_hours=24)
        assert len(stories) == 1
        assert stories[0]["title"] == "Good Story"

    @patch("src.bbc_noticias.rss.requests.get")
    def test_handles_multiple_feeds(self, mock_get):
        mock_get.return_value.__enter__.return_value.status_code = 200
        mock_get.return_value.__enter__.return_value.content = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Feed A</title>
    <item>
      <title>From Feed A</title>
      <link>https://a.com/story</link>
      <pubDate>Fri, 08 May 2026 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""

        stories = fetch_stories(max_age_hours=24)
        assert len(stories) == 1
        assert stories[0]["title"] == "From Feed A"