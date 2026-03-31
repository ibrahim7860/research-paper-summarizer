"""
Interactive script to create a human-labeled test set for prompt optimization.

Fetches recent papers and asks you to rate each one. Saves the labeled set
to eval/test_set.json for use by evaluate.py.

Usage:
    uv run python eval/create_test_set.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import load_config
from src.fetchers import ArxivFetcher

TEST_SET_PATH = Path(__file__).parent / "test_set.json"


def load_existing() -> list[dict]:
    if TEST_SET_PATH.exists():
        with open(TEST_SET_PATH) as f:
            return json.load(f)
    return []


def save_test_set(papers: list[dict]) -> None:
    with open(TEST_SET_PATH, "w") as f:
        json.dump(papers, f, indent=2)
    print(f"\nSaved {len(papers)} papers to {TEST_SET_PATH}")


def main() -> None:
    existing = load_existing()
    existing_titles = {p["title"].lower().strip() for p in existing}
    print(f"Existing test set: {len(existing)} papers")
    print()

    # Fetch recent papers from arXiv
    print("Fetching recent papers from arXiv (cs.AI, cs.LG)...")
    fetcher = ArxivFetcher(categories=["cs.AI", "cs.LG"], max_results_per_category=20)
    papers = fetcher.fetch_recent(days_back=3)
    print(f"Fetched {len(papers)} papers\n")

    new_papers = [p for p in papers if p.title.lower().strip() not in existing_titles]
    if not new_papers:
        print("No new papers to label.")
        return

    print("=" * 60)
    print("Rate each paper 1-10 for relevance to building AI applications.")
    print("Enter 's' to skip, 'q' to quit and save.\n")
    print("HIGH (8-10): New technique/tool you could build with")
    print("MED  (5-7):  Useful insights, may need adaptation")
    print("LOW  (1-4):  Purely theoretical, benchmarks only")
    print("=" * 60)

    labeled = list(existing)

    for i, paper in enumerate(new_papers):
        print(f"\n--- Paper {len(labeled) + 1} ({i + 1}/{len(new_papers)}) ---")
        print(f"Title: {paper.title}")
        print(f"Abstract: {paper.abstract[:300]}...")
        print()

        while True:
            score_input = input("Score (1-10, s=skip, q=quit): ").strip().lower()
            if score_input == "q":
                save_test_set(labeled)
                return
            if score_input == "s":
                break
            try:
                score = int(score_input)
                if 1 <= score <= 10:
                    labeled.append(
                        {
                            "title": paper.title,
                            "abstract": paper.abstract,
                            "human_score": score,
                            "should_include": score >= 7,
                            "source": paper.source,
                            "url": paper.url,
                        }
                    )
                    print(f"  → Recorded score {score}")
                    break
                else:
                    print("  Please enter 1-10.")
            except ValueError:
                print("  Please enter a number 1-10, 's', or 'q'.")

    save_test_set(labeled)


if __name__ == "__main__":
    main()
