"""
Text simplifier — takes raw Spanish article text and returns a B1-adapted version.
Calls OpenRouter with SIMPLIFY_PROMPT: simplifies sentence structures
and adds English translations for difficult words.
"""
from .llm import LLM
from .prompts import SIMPLIFY_PROMPT, DORIAN_PROFILE


def simplify_article(article_text: str, llm: LLM) -> str:
    """
    Given the full Spanish article text, call OpenRouter to produce
    a B1-adapted version with:
      - simpler sentence structures
      - English translations in (parentheses) for difficult words
    """
    # Truncate if too long (OpenRouter has context limits and high costs)
    MAX_CHARS = 6000
    if len(article_text) > MAX_CHARS:
        article_text = article_text[:MAX_CHARS] + "\n[... texto truncado ...]"

    prompt = SIMPLIFY_PROMPT.format(
        profile=DORIAN_PROFILE,
        article_text=article_text,
    )

    simplified = llm.complete(
        system=(
            "You are a Spanish language tutor. Always respond with ONLY the "
            "simplified Spanish text. Never add explanations, preambles, "
            "or anything outside the article text itself."
        ),
        user=prompt,
        temperature=0.6,
    )
    return simplified