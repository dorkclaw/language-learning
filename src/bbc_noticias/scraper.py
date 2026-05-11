"""
Article scraper — fetches a BBC Mundo article URL and extracts readable text.
Uses basic regex + HTML parsing to strip navigation/clutter.
"""
import re
import requests
from typing import Optional

# BBC Mundo uses this User-Agent to get the article page
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9",
}


def fetch_article(url: str, timeout: int = 15) -> Optional[str]:
    """
    Fetch a BBC Mundo article and return the main body text as plain Spanish.
    Returns None on failure.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        html = resp.text

        # Extract the <article> body via a simple approach:
        # BBC uses <article data-component="article-body"> ... </article>
        body = _extract_article_body(html)
        if not body:
            # Fallback: grab everything between two common article markers
            body = _fallback_extract(html)

        if not body:
            return None

        # Clean up: strip tags, normalize whitespace
        text = _clean_html(body)
        return text if text else None

    except Exception as e:
        print(f"[scraper] Failed to fetch {url}: {e}")
        return None


def _extract_article_body(html: str) -> Optional[str]:
    """Try to extract the main article body via data-component or class markers."""
    # Pattern 1: <article ...> ... </article>
    m = re.search(r'<article[^>]*>(.*?)</article>', html, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1)

    # Pattern 2: data-component="article-body"
    m = re.search(
        r'<div[^>]*data-component="article-body"[^>]*>(.*?)</div>',
        html, re.DOTALL | re.IGNORECASE
    )
    if m:
        return m.group(1)

    # Pattern 3: section with id="body-content"
    m = re.search(
        r'<section[^>]*id="body-content"[^>]*>(.*?)</section>',
        html, re.DOTALL | re.IGNORECASE
    )
    if m:
        return m.group(1)

    return None


def _fallback_extract(html: str) -> Optional[str]:
    """Last-resort extraction from main content area."""
    m = re.search(r'<main[^>]*>(.*?)</main>', html, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1)
    return None


def _clean_html(html: str) -> str:
    """Remove HTML tags and normalize whitespace from article body."""
    # Remove script, style, nav, footer, aside
    html = re.sub(r'<(script|style|nav|footer|aside|form)[^>]*>.*?</\1>',
                  '', html, flags=re.DOTALL | re.IGNORECASE)
    # Replace block elements with newlines
    html = re.sub(r'<(p|div|br|h[1-6]|li|blockquote)[^>]*>', '\n', html, flags=re.IGNORECASE)
    # Strip remaining tags
    html = re.sub(r'<[^>]+>', '', html)
    # Decode common HTML entities
    html = html.replace('\u00a0', ' ')
    for entity, char in [('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>'),
                         ('&quot;', '"'), ('&#39;', "'"), ('&ntilde;', 'ñ'),
                         ('&Ntilde;', 'Ñ'), ('&uuml;', 'ü'), ('&aacute;', 'á'),
                         ('&eacute;', 'é'), ('&iacute;', 'í'), ('&oacute;', 'ó'),
                         ('&uacute;', 'ú'), ('&iexcl;', '¡'), ('&iquest;', '¿')]:
        html = html.replace(entity, char)
    # Normalize whitespace: collapse multiple spaces, strip line ends
    html = re.sub(r' {2,}', ' ', html)
    lines = [ln.strip() for ln in html.splitlines()]
    return '\n'.join(ln for ln in lines if ln)


if __name__ == "__main__":
    # Quick smoke test
    url = "https://www.bbc.com/mundo/articles/c4gl71dez8zo"
    text = fetch_article(url)
    print(text[:500] if text else "No article text found")