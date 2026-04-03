from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import anthropic

from src.fetchers.base import Paper

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "scoring_prompt.txt"


def load_prompt_template() -> str:
    return PROMPT_PATH.read_text()


def score_paper(client: anthropic.Anthropic, paper: Paper, model: str = "claude-haiku-4-5-20251001") -> dict | None:
    """Score and summarize a single paper. Returns dict with relevance_score, one_liner, summary, key_takeaway."""
    template = load_prompt_template()
    prompt = template.replace("{title}", paper.title).replace("{abstract}", paper.abstract)

    for attempt in range(3):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()

            # Handle potential markdown code fences
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON for '{paper.title}': {text[:200]}")
            return None
        except anthropic.RateLimitError:
            wait = 2 ** (attempt + 1)
            logger.warning(f"Rate limited, waiting {wait}s...")
            time.sleep(wait)
        except Exception:
            logger.exception(f"Error scoring paper '{paper.title}'")
            return None

    return None


def score_papers(
    papers: list[Paper],
    api_key: str,
    model: str = "claude-haiku-4-5-20251001",
) -> list[tuple[Paper, dict]]:
    """Score all papers and return (paper, result) tuples for papers that scored successfully."""
    client = anthropic.Anthropic(api_key=api_key)
    results: list[tuple[Paper, dict]] = []

    for i, paper in enumerate(papers):
        logger.info(f"Scoring paper {i + 1}/{len(papers)}: {paper.title[:60]}...")
        result = score_paper(client, paper, model)
        if result and isinstance(result.get("relevance_score"), (int, float)):
            results.append((paper, result))
        time.sleep(0.5)  # be nice to the API

    logger.info(f"Scored {len(results)}/{len(papers)} papers successfully")
    return results
