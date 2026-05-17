"""
Smoke tests — verify that all modules import cleanly without API keys or network.

Run with:
    python3 -m pytest tests/test_imports.py -v
"""
import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock
from importlib import import_module

# ---------------------------------------------------------------------------
# conftest already mocks requests + dotenv.
# This module additionally mocks discord and any other optional deps,
# then verifies every bbc_noticias module can be imported.
# ---------------------------------------------------------------------------

# Mock discord (not installed in test env)
sys.modules["discord"] = MagicMock()
sys.modules["discord.ext.commands"] = MagicMock()
sys.modules["discord_slash"] = MagicMock()
sys.modules["slash"] = MagicMock()

# Mock openai (LLM dependency)
mock_openai = MagicMock()
sys.modules["openai"] = mock_openai


# ---------------------------------------------------------------------------
# Test: every public function imported from simplifier.py actually exists
# ---------------------------------------------------------------------------
def test_simplifier_exports_exist():
    """Verify every function that discord_bot.py imports from simplifier actually exists."""
    from src.bbc_noticias import simplifier

    # These are the functions discord_bot.py imports from simplifier
    expected = {"simplify_article"}
    actual = set(dir(simplifier))
    missing = expected - actual
    assert not missing, f"simplifier.py is missing exports that other modules import: {missing}"


# ---------------------------------------------------------------------------
# Test: discord_bot.py imports cleanly (catches simplify_story typo)
# ---------------------------------------------------------------------------
def test_discord_bot_imports_cleanly():
    """Verify discord_bot.py imports without AttributeError or ImportError.

    This test would have caught the simplify_story typo:
    - discord_bot.py imported: from simplifier import simplify_story
    - simplify_story does not exist → ImportError or AttributeError
    """
    # Patch the token check so bot doesn't try to connect
    import src.bbc_noticias.discord_bot as discord_bot_mod

    # The module should load without raising ImportError
    # We only check that the imports at the top of the file succeed
    assert discord_bot_mod is not None


# ---------------------------------------------------------------------------
# Test: all bbc_noticias modules import cleanly
# ---------------------------------------------------------------------------
def test_all_bbc_noticias_modules_import():
    """Verify every module in src/bbc_noticias/ can be imported."""
    from src.bbc_noticias import (
        bot,
        config,
        llm,
        notifier,
        prompts,
        rss,
        scraper,
        selector,
        sent_stories,
        simplifier,
        queue,
        discord_bot,
    )
    # All should be real modules, not None
    assert bot is not None
    assert config is not None
    assert llm is not None
    assert notifier is not None
    assert prompts is not None
    assert rss is not None
    assert scraper is not None
    assert selector is not None
    assert sent_stories is not None
    assert simplifier is not None
    assert queue is not None
    assert discord_bot is not None


# ---------------------------------------------------------------------------
# Test: queue functions are callable and work with temp storage
# ---------------------------------------------------------------------------
def test_queue_basic_operations(tmp_path):
    """Verify queue enqueue/pop/peek work with a temp file."""
    import src.bbc_noticias.queue as queue_mod

    original_path = queue_mod.QUEUE_PATH
    tmp_queue = tmp_path / "queue.json"
    queue_mod.QUEUE_PATH = tmp_queue

    try:
        from src.bbc_noticias.queue import enqueue_story, pop_story, pending_count, peek_pending

        story = {
            "title": "Test Story",
            "link": "https://bbc.com/test",
            "source": "BBC",
            "pub_date": "2026-05-17T08:00:00Z",
        }

        # Peek empty queue
        assert pending_count() == 0
        assert peek_pending() == []

        # Enqueue
        enqueue_story(story)
        assert pending_count() == 1

        # Pop
        popped = pop_story()
        assert popped["title"] == "Test Story"
        assert popped["link"] == "https://bbc.com/test"

        # Queue now empty
        assert pending_count() == 0
        assert pop_story() is None

    finally:
        queue_mod.QUEUE_PATH = original_path


# ---------------------------------------------------------------------------
# Test: bot.py calls enqueue_story after sending (smoke test)
# ---------------------------------------------------------------------------
def test_bot_enqueues_after_send(tmp_path):
    """Verify bot.py calls enqueue_story when a story is sent.

    This is a compile-check: verify the call is present in bot.py source.
    """
    bot_src = (Path(__file__).parent.parent / "src" / "bbc_noticias" / "bot.py").read_text()
    assert "enqueue_story" in bot_src, "bot.py should call enqueue_story after send_article"