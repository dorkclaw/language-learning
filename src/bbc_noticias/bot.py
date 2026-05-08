"""
BBC Noticias Bot — main entrypoint.

Fetches BBC Mundo RSS → selects most relevant story for Dorian via OpenRouter →
fetches & simplifies the article → sends to Discord and/or Telegram.

Run once:
    python -m src.bbc_noticias.bot

Run on a schedule (Docker):
    python -m src.bbc_noticias.bot --loop --interval 24
"""
import argparse
import sys
import time
from pathlib import Path

# Allow running from repo root or project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.bbc_noticias.rss import fetch_stories
from src.bbc_noticias.scraper import fetch_article
from src.bbc_noticias.selector import select_best_story
from src.bbc_noticias.simplifier import simplify_article
from src.bbc_noticias.notifier import send_article
from src.bbc_noticias.config import load


def run() -> bool:
    cfg = load()

    print("\n=== BBC Noticias Bot ===")
    print(f"Model: {cfg.openrouter_model}")
    print(f"Dry run: {cfg.dry_run}")

    # 1. Fetch RSS
    print("\n[1/4] Fetching RSS feeds...")
    stories = fetch_stories(max_age_hours=cfg.max_age_hours)
    print(f"  Found {len(stories)} stories from the last {cfg.max_age_hours}h.")
    if not stories:
        print("  No recent stories found. Exiting.")
        return False

    # Limit for the selection prompt
    stories = stories[: cfg.max_stories_for_selection]

    # 2. Select best story
    print("\n[2/4] Selecting most relevant story...")
    from src.bbc_noticias.llm import LLM

    try:
        llm = LLM()
    except ValueError as e:
        print(f"  LLM init failed: {e}")
        return False

    best = select_best_story(stories, llm)
    if not best:
        print("  Could not select a story. Exiting.")
        return False
    print(f"  Selected: {best['title']}")
    print(f"  URL: {best['link']}")

    # 3. Fetch & simplify article
    print("\n[3/4] Fetching article and simplifying text...")
    article_text = fetch_article(best["link"])
    if not article_text:
        print("  Could not fetch article text. Exiting.")
        return False
    print(f"  Fetched {len(article_text)} characters.")

    simplified = simplify_article(article_text, llm)
    print(f"  Simplified {len(simplified)} characters.")

    if cfg.dry_run:
        print("\n[dry-run] Would have sent:")
        print(f"  Title: {best['title']}")
        print(f"  Link: {best['link']}")
        print(f"  Text:\n{simplified[:500]}...")
        return True

    # 4. Notify
    print("\n[4/4] Sending article to channels...")
    result = send_article(
        title=best["title"],
        original_url=best["link"],
        simplified_text=simplified,
        pub_date=best["pub_date"],
    )
    print(f"  Discord: {'✅' if result['discord'] else '❌'}")
    print(f"  Telegram: {'✅' if result['telegram'] else '❌'}")
    return True


def run_loop(interval_hours: float = 24):
    """Run the bot on a schedule."""
    while True:
        success = run()
        if success:
            print(f"\nSleeping for {interval_hours}h...")
        else:
            print("\n[warning] Previous run failed. Retrying sooner (1h)...")
        time.sleep(3600 if not success else interval_hours * 3600)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BBC Noticias language learning bot")
    parser.add_argument(
        "--loop", action="store_true", help="Run continuously on a schedule"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=24,
        help="Hours between runs in loop mode (default: 24)",
    )
    args = parser.parse_args()

    if args.loop:
        run_loop(args.interval)
    else:
        run()