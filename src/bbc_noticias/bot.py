"""
BBC Noticias Bot — main entrypoint.

Fetches BBC Mundo RSS → selects most relevant story for Dorian via OpenRouter →
fetches & simplifies the article → sends to Discord and/or Telegram.

Run once (how it works with cron):
    python -m src.bbc_noticias.bot

For cron: schedule this script to run once a day via your system's cron,
docker-compose cron, or OpenClaw's built-in cron.
"""

import logging

from dotenv import load_dotenv

load_dotenv()

from src.bbc_noticias.rss import fetch_stories
from src.bbc_noticias.scraper import fetch_article
from src.bbc_noticias.selector import select_best_story
from src.bbc_noticias.simplifier import simplify_article
from src.bbc_noticias.notifier import send_article
from src.bbc_noticias.sent_stories import filter_unsent
from src.bbc_noticias.config import load


def run() -> bool:
    cfg = load()
    log = logging.getLogger("bot")
    log.info("BBC Noticias Bot — model: %s, dry_run: %s", cfg.openrouter_model, cfg.dry_run)

    # 1. Fetch RSS
    log.info("[1/4] Fetching RSS feeds...")
    stories = fetch_stories(max_age_hours=cfg.max_age_hours)
    log.info("  Found %d stories from the last %dh.", len(stories), cfg.max_age_hours)
    if not stories:
        log.warning("  No recent stories found. Exiting.")
        return False

    # Limit for the selection prompt
    stories = stories[: cfg.max_stories_for_selection]

    # Filter out stories we've already sent (unless we're in dry-run mode)
    unsent_links = set(filter_unsent([s["link"] for s in stories]))
    stories = [s for s in stories if s["link"] in unsent_links]
    if not stories:
        print("  All recent stories have already been sent. Exiting.")
        return False

    # 2. Select best story
    log.info("[2/4] Selecting most relevant story...")
    from src.bbc_noticias.llm import LLM

    try:
        llm = LLM()
    except ValueError as e:
        log.error("  LLM init failed: %s", e)
        return False

    best = select_best_story(stories, llm)
    if not best:
        log.warning("  Could not select a story. Exiting.")
        return False
    log.info("  Selected: %s | %s", best["title"], best["link"])

    # 3. Fetch & simplify article
    log.info("[3/4] Fetching article and simplifying text...")
    article_text = fetch_article(best["link"])
    if not article_text:
        log.error("  Could not fetch article text. Exiting.")
        return False
    log.info("  Fetched %d characters.", len(article_text))

    simplified = simplify_article(article_text, llm)
    log.info("  Simplified %d characters.", len(simplified))

    if cfg.dry_run:
        log.info("[dry-run] Would have sent — title: %s | link: %s", best["title"], best["link"])
        log.debug("  Text preview (500 chars): %s...", simplified[:500])
        return True

    # 4. Notify
    log.info("[4/4] Sending article to channels...")
    result = send_article(
        title=best["title"],
        original_url=best["link"],
        simplified_text=simplified,
        pub_date=best["pub_date"],
    )
    log.info("  Discord: %s | Telegram: %s", "✅" if result["discord"] else "❌", "✅" if result["telegram"] else "❌")

    # Also enqueue for the Discord bot (shares queue via volume)
    if result["discord"] or result["telegram"]:
        from src.bbc_noticias.queue import enqueue_story
        enqueue_story(best)

    return True


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )
    run()