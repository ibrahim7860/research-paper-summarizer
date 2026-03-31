from __future__ import annotations

import logging
import sys

from src.config import load_config
from src.emailer import render_digest, send_email
from src.fetchers import ArxivFetcher, PapersWithCodeFetcher, SemanticScholarFetcher
from src.fetchers.base import Paper
from src.storage import PaperStorage
from src.summarizer import score_papers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def fetch_all(config: dict) -> list[Paper]:
    """Fetch papers from all enabled sources."""
    papers: list[Paper] = []
    sources = config.get("sources", {})
    days_back = config.get("schedule", {}).get("days_back", 1)

    if sources.get("arxiv", {}).get("enabled", True):
        arxiv_cfg = sources["arxiv"]
        fetcher = ArxivFetcher(
            categories=arxiv_cfg.get("categories", ["cs.AI"]),
            max_results_per_category=arxiv_cfg.get("max_results_per_category", 30),
        )
        papers.extend(fetcher.fetch_recent(days_back))

    if sources.get("semantic_scholar", {}).get("enabled", True):
        ss_cfg = sources["semantic_scholar"]
        fetcher = SemanticScholarFetcher(keywords=ss_cfg.get("keywords", ["AI agents"]))
        papers.extend(fetcher.fetch_recent(days_back))

    if sources.get("papers_with_code", {}).get("enabled", True):
        fetcher = PapersWithCodeFetcher()
        papers.extend(fetcher.fetch_recent(days_back))

    return papers


def deduplicate(papers: list[Paper], storage: PaperStorage) -> list[Paper]:
    """Remove papers already seen and deduplicate by normalized title."""
    seen_titles: set[str] = set()
    unique: list[Paper] = []

    for paper in papers:
        nt = paper.normalized_title
        if nt in seen_titles or storage.is_seen(nt):
            continue
        seen_titles.add(nt)
        unique.append(paper)

    logger.info(f"Deduplication: {len(papers)} → {len(unique)} papers")
    return unique


def main() -> None:
    config = load_config()
    storage = PaperStorage(config["storage"]["db_path"])

    try:
        # 1. Fetch
        logger.info("=== Fetching papers ===")
        papers = fetch_all(config)

        # 2. Deduplicate
        logger.info("=== Deduplicating ===")
        papers = deduplicate(papers, storage)

        if not papers:
            logger.info("No new papers found. Exiting.")
            return

        # 3. Score and summarize
        logger.info(f"=== Scoring {len(papers)} papers ===")
        scored = score_papers(papers, api_key=config["anthropic_api_key"])

        # 4. Store all papers (including those that failed scoring)
        scored_titles = {paper.normalized_title for paper, _ in scored}
        for paper in papers:
            if paper.normalized_title in scored_titles:
                result = next(r for p, r in scored if p.normalized_title == paper.normalized_title)
                storage.mark_seen(
                    external_id=paper.external_id,
                    normalized_title=paper.normalized_title,
                    title=paper.title,
                    source=paper.source,
                    summary=result.get("summary", ""),
                    relevance_score=result.get("relevance_score", 0),
                    key_takeaway=result.get("key_takeaway", ""),
                )
            else:
                storage.mark_seen(
                    external_id=paper.external_id,
                    normalized_title=paper.normalized_title,
                    title=paper.title,
                    source=paper.source,
                    summary="",
                    relevance_score=0,
                    key_takeaway="",
                )

        # 5. Filter
        threshold = config.get("filtering", {}).get("relevance_threshold", 7)
        max_papers = config.get("filtering", {}).get("max_papers_per_digest", 20)
        filtered = [(p, r) for p, r in scored if r.get("relevance_score", 0) >= threshold]
        filtered.sort(key=lambda x: x[1].get("relevance_score", 0), reverse=True)
        filtered = filtered[:max_papers]

        logger.info(f"Filtered: {len(filtered)} papers pass threshold ({threshold}+)")

        if not filtered:
            logger.info("No papers passed the relevance threshold. No email sent.")
            return

        # 6. Email
        logger.info("=== Sending email digest ===")
        html = render_digest(filtered, threshold=threshold)

        email_cfg = config.get("email", {})
        send_email(
            html_body=html,
            smtp_host=email_cfg.get("smtp_host", "smtp.gmail.com"),
            smtp_port=email_cfg.get("smtp_port", 587),
            sender=email_cfg["sender"],
            password=config["smtp_password"],
            recipients=email_cfg["recipients"],
            subject_prefix=email_cfg.get("subject_prefix", "[Paper Digest]"),
        )

        logger.info("=== Done ===")
        logger.info(f"Total fetched: {len(papers)} | Scored: {len(scored)} | Emailed: {len(filtered)}")

    finally:
        storage.close()


if __name__ == "__main__":
    main()
