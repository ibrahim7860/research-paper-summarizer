from __future__ import annotations

import logging
import os
import time
from datetime import date, timedelta

import requests

from src.fetchers.base import BaseFetcher, Paper

logger = logging.getLogger(__name__)

API_BASE = "https://api.semanticscholar.org/graph/v1"
FIELDS = "title,abstract,authors,url,externalIds,publicationDate,fieldsOfStudy,openAccessPdf"


class SemanticScholarFetcher(BaseFetcher):
    def __init__(self, keywords: list[str]):
        self.keywords = keywords
        self.api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")

    def fetch_recent(self, days_back: int = 1) -> list[Paper]:
        cutoff = date.today() - timedelta(days=days_back)
        date_range = f"{cutoff}:{date.today()}"
        papers: list[Paper] = []
        seen_ids: set[str] = set()

        for keyword in self.keywords:
            logger.info(f"Semantic Scholar search: {keyword}")
            try:
                results = self._search(keyword, date_range)
                for paper in results:
                    if paper.external_id not in seen_ids:
                        seen_ids.add(paper.external_id)
                        papers.append(paper)
                time.sleep(3)  # rate limit
            except Exception:
                logger.exception(f"Failed Semantic Scholar search: {keyword}")

        logger.info(f"Semantic Scholar: fetched {len(papers)} unique papers")
        return papers

    def _search(self, query: str, date_range: str) -> list[Paper]:
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        for attempt in range(3):
            resp = requests.get(
                f"{API_BASE}/paper/search",
                params={
                    "query": query,
                    "fields": FIELDS,
                    "limit": 50,
                    "publicationDateOrYear": date_range,
                    "fieldsOfStudy": "Computer Science",
                },
                headers=headers,
                timeout=30,
            )
            if resp.status_code == 429:
                wait = 3 * (attempt + 1)
                logger.warning(f"Semantic Scholar rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            break
        else:
            logger.warning(f"Semantic Scholar: gave up after 3 rate-limit retries for '{query}'")
            return []

        data = resp.json()

        papers: list[Paper] = []
        for item in data.get("data", []):
            if not item.get("abstract"):
                continue

            arxiv_id = None
            external_ids = item.get("externalIds") or {}
            if external_ids.get("ArXiv"):
                arxiv_id = external_ids["ArXiv"]

            pdf_url = None
            oap = item.get("openAccessPdf")
            if oap:
                pdf_url = oap.get("url")

            pub_date = None
            if item.get("publicationDate"):
                try:
                    pub_date = date.fromisoformat(item["publicationDate"])
                except ValueError:
                    pass

            authors = [a["name"] for a in (item.get("authors") or []) if a.get("name")]

            papers.append(
                Paper(
                    source="semantic_scholar",
                    external_id=item.get("paperId", arxiv_id or item.get("title", "")),
                    title=item["title"],
                    authors=authors,
                    abstract=item["abstract"],
                    url=item.get("url", ""),
                    pdf_url=pdf_url,
                    published_date=pub_date,
                    categories=item.get("fieldsOfStudy") or [],
                )
            )

        return papers
