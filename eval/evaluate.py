"""
Evaluation harness for the autoresearch prompt optimization loop.

Loads the current scoring prompt, runs it against a fixed test set of
human-labeled papers, and outputs a composite metric to stdout.

Usage:
    uv run python eval/evaluate.py
"""

from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic
import numpy as np
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
PROMPT_PATH = ROOT / "prompts" / "scoring_prompt.txt"
TEST_SET_PATH = ROOT / "eval" / "test_set.json"
RESULTS_PATH = ROOT / "eval" / "results.tsv"


def load_test_set() -> list[dict]:
    with open(TEST_SET_PATH) as f:
        return json.load(f)


def load_prompt() -> str:
    return PROMPT_PATH.read_text()


def score_one(client: anthropic.Anthropic, prompt_template: str, paper: dict) -> dict | None:
    prompt = prompt_template.replace("{title}", paper["title"]).replace("{abstract}", paper["abstract"])
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
        return json.loads(text)
    except Exception as e:
        logger.warning(f"Failed to score '{paper['title'][:50]}': {e}")
        return None


def spearman_correlation(x: list[float], y: list[float]) -> float:
    """Compute Spearman rank correlation between two lists."""
    n = len(x)
    if n < 3:
        return 0.0

    def _rank(vals: list[float]) -> list[float]:
        indexed = sorted(enumerate(vals), key=lambda t: t[1])
        ranks = [0.0] * n
        for rank, (orig_idx, _) in enumerate(indexed):
            ranks[orig_idx] = float(rank)
        return ranks

    rx = _rank(x)
    ry = _rank(y)

    d_sq = sum((a - b) ** 2 for a, b in zip(rx, ry))
    return 1.0 - (6.0 * d_sq) / (n * (n * n - 1))


def classification_accuracy(
    predicted_scores: list[float],
    human_include: list[bool],
    threshold: int = 7,
) -> float:
    """Accuracy of include/exclude classification at the given threshold."""
    if not predicted_scores:
        return 0.0
    correct = sum(
        1
        for score, should_include in zip(predicted_scores, human_include)
        if (score >= threshold) == should_include
    )
    return correct / len(predicted_scores)


def run_evaluation() -> float:
    """Run the full evaluation and return the composite score."""
    test_set = load_test_set()
    prompt_template = load_prompt()
    client = anthropic.Anthropic()

    predicted_scores: list[float] = []
    human_scores: list[float] = []
    human_include: list[bool] = []
    successes = 0

    for i, paper in enumerate(test_set):
        result = score_one(client, prompt_template, paper)
        if result and isinstance(result.get("relevance_score"), (int, float)):
            predicted_scores.append(float(result["relevance_score"]))
            human_scores.append(float(paper["human_score"]))
            human_include.append(paper.get("should_include", paper["human_score"] >= 7))
            successes += 1
        time.sleep(0.3)

    if successes < 5:
        print(f"composite_score: 0.0 (only {successes} successful scores)")
        return 0.0

    # Compute metrics
    rank_corr = spearman_correlation(predicted_scores, human_scores)
    cls_acc = classification_accuracy(predicted_scores, human_include)

    # Composite: 60% rank correlation + 40% classification accuracy
    composite = 0.6 * max(rank_corr, 0.0) + 0.4 * cls_acc

    # Log to results.tsv
    prompt_hash = hash(prompt_template) % (10**8)
    _log_result(prompt_hash, composite, rank_corr, cls_acc, successes, len(test_set))

    print(f"composite_score: {composite:.4f}")
    print(f"  rank_correlation: {rank_corr:.4f}")
    print(f"  classification_accuracy: {cls_acc:.4f}")
    print(f"  scored: {successes}/{len(test_set)}")

    return composite


def _log_result(
    prompt_hash: int,
    composite: float,
    rank_corr: float,
    cls_acc: float,
    successes: int,
    total: int,
) -> None:
    header_needed = not RESULTS_PATH.exists()
    with open(RESULTS_PATH, "a") as f:
        if header_needed:
            f.write("timestamp\tprompt_hash\tcomposite\trank_corr\tcls_acc\tscored\ttotal\n")
        f.write(
            f"{datetime.utcnow().isoformat()}\t{prompt_hash}\t{composite:.4f}\t"
            f"{rank_corr:.4f}\t{cls_acc:.4f}\t{successes}\t{total}\n"
        )


if __name__ == "__main__":
    run_evaluation()
