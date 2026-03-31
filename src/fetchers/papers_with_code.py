from __future__ import annotations

import logging
from datetime import date, timedelta

import requests

from src.fetchers.base import BaseFetcher, Paper

logger = logging.getLogger(__name__)

API_BASE = "https://paperswithcode.com/api/v1"


class PapersWithCodeFetcher(BaseFetcher):
    def fetch_recent(self, days_back: int = 1) -> list[Paper]:
        cutoff = date.today() - timedelta(days=days_back)
        papers: list[Paper] = []

        try:
            page = 1
            while page <= 3:  # max 3 pages to avoid excessive requests
                resp = requests.get(
                    f"{API_BASE}/papers/",
                    params={"ordering": "-published", "page": page, "items_per_page": 50},
                    timeout=30,
                )
                resp.raise_for_status()
                if not resp.text.strip():
                    logger.warning("Papers With Code returned empty response")
                    break
                data = resp.json()
                results = data.get("results", [])

                if not results:
                    break

                for item in results:
                    pub_date = None
                    if item.get("published"):
                        try:
                            pub_date = date.fromisoformat(item["published"][:10])
                        except ValueError:
                            continue

                    if pub_date and pub_date < cutoff:
                        return papers  # papers are sorted by date, stop early

                    abstract = item.get("abstract", "")
                    if not abstract:
                        continue

                    code_url = None
                    if item.get("repositories"):
                        repos = item["repositories"]
                        if repos:
                            code_url = repos[0].get("url")

                    papers.append(
                        Paper(
                            source="papers_with_code",
                            external_id=item.get("id", item.get("title", "")),
                            title=item.get("title", ""),
                            authors=[a for a in (item.get("authors") or [])],
                            abstract=abstract,
                            url=item.get("url_abs", item.get("paper_url", "")),
                            pdf_url=item.get("url_pdf"),
                            published_date=pub_date,
                            code_url=code_url,
                        )
                    )

                page += 1

        except Exception:
            logger.exception("Failed to fetch from Papers With Code")

        logger.info(f"Papers With Code: fetched {len(papers)} papers")
        return papers
