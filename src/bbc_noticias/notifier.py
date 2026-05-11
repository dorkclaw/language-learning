"""
Notifier — dispatches the simplified article to Discord and/or Telegram.
Configuration via environment variables (see .env.example).

Discord:
  DISCORD_WEBHOOK_URL  — full webhook URL (get it from Discord channel settings > Integrations > Webhooks)

Telegram:
  TELEGRAM_BOT_TOKEN   — bot token from @BotFather
  TELEGRAM_CHAT_ID     — numeric chat ID (channel, group, or DM)
"""
import os
import requests
from typing import Optional


def _discord_post(content: str) -> bool:
    url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not url:
        return False

    # Discord max content length is 2000; send as multiple messages if needed
    if len(content) <= 2000:
        data = {"content": content}
        try:
            resp = requests.post(url, json=data, timeout=10)
            if resp.status_code in (200, 204):
                return True
            print(f"[discord] HTTP {resp.status_code}: {resp.text[:200]}")
            return False
        except Exception as e:
            print(f"[discord] Error: {e}")
            return False
    else:
        # Split into chunks of 1990 chars and send each as a separate message
        all_ok = True
        for i in range(0, len(content), 1990):
            chunk = content[i : i + 1990]
            data = {"content": f"```\n{chunk}\n```"}
            try:
                resp = requests.post(url, json=data, timeout=10)
                if resp.status_code not in (200, 204):
                    print(f"[discord] chunk {i}: HTTP {resp.status_code}")
                    all_ok = False
            except Exception as e:
                print(f"[discord] chunk {i}: {e}")
                all_ok = False
        return all_ok


def _telegram_post(content: str, parse_mode: Optional[str] = "MarkdownV2") -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # Telegram message length limit is 4096 chars
    MAX_MSG = 4090

    def send_chunk(chunk: str) -> bool:
        data = {"chat_id": chat_id, "text": chunk}
        if parse_mode:
            data["parse_mode"] = parse_mode
        try:
            resp = requests.post(url, json=data, timeout=10)
            if resp.status_code == 200:
                return True
            print(f"[telegram] HTTP {resp.status_code}: {resp.text[:200]}")
            return False
        except Exception as e:
            print(f"[telegram] Error: {e}")
            return False

    if len(content) <= MAX_MSG:
        return send_chunk(content)
    else:
        all_ok = True
        for i in range(0, len(content), MAX_MSG):
            chunk = content[i : i + MAX_MSG]
            if not send_chunk(chunk):
                all_ok = False
        return all_ok


def send_article(
    title: str,
    original_url: str,
    simplified_text: str,
    pub_date: Optional[str] = None,
) -> dict:
    """
    Compose and send the article to all configured channels.
    Returns a dict with delivery status per channel.
    """
    # Format the message
    header = f"📰 *BBC Mundo — Artículo del día*\n\n*{title}*\n"
    if pub_date:
        header += f"_Publicado: {pub_date[:10]}_\n"
    header += f"🔗 {original_url}\n\n"
    footer = "\n\n_¿Te gusta este formato? Reacciona con ✅ o dime qué cambiar._"

    content = f"{header}{simplified_text}{footer}"

    discord_ok = _discord_post(content)
    telegram_ok = _telegram_post(content)

    # Try plain text for Telegram if Markdown fails
    if not telegram_ok and content != f"{header}{simplified_text}{footer}".replace("*", "").replace("_", ""):
        plain = f"{header}{simplified_text}{footer}".replace("*", "").replace("_", "")
        telegram_ok = _telegram_post(plain, parse_mode=None)

    return {"discord": discord_ok, "telegram": telegram_ok}