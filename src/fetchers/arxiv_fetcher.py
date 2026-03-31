from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

import arxiv

from src.fetchers.base import BaseFetcher, Paper

logger = logging.getLogger(__name__)


class ArxivFetcher(BaseFetcher):
    def __init__(self, categories: list[str], max_results_per_category: int = 30):
        self.categories = categories
        self.max_results_per_category = max_results_per_category

    def fetch_recent(self, days_back: int = 1) -> list[Paper]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
        papers: list[Paper] = []
        seen_ids: set[str] = set()

        for category in self.categories:
            logger.info(f"Fetching arXiv category: {category}")
            try:
                results = self._fetch_category(category, cutoff)
                for paper in results:
                    if paper.external_id not in seen_ids:
                        seen_ids.add(paper.external_id)
                        papers.append(paper)
            except Exception:
                logger.exception(f"Failed to fetch arXiv category {category}")

        logger.info(f"arXiv: fetched {len(papers)} unique papers")
        return papers

    def _fetch_category(self, category: str, cutoff: datetime) -> list[Paper]:
        client = arxiv.Client()
        search = arxiv.Search(
            query=f"cat:{category}",
            max_results=self.max_results_per_category,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        papers: list[Paper] = []
        for result in client.results(search):
            published = result.published.replace(tzinfo=timezone.utc)
            if published < cutoff:
                break

            papers.append(
                Paper(
                    source="arxiv",
                    external_id=result.entry_id,
                    title=result.title,
                    authors=[a.name for a in result.authors],
                    abstract=result.summary,
                    url=result.entry_id,
                    pdf_url=result.pdf_url,
                    published_date=published.date(),
                    categories=[c for c in result.categories],
                )
            )

        return papers
