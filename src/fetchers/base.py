from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date


@dataclass
class Paper:
    source: str
    external_id: str
    title: str
    authors: list[str]
    abstract: str
    url: str
    pdf_url: str | None = None
    published_date: date | None = None
    categories: list[str] = field(default_factory=list)
    code_url: str | None = None

    @property
    def normalized_title(self) -> str:
        return " ".join(self.title.lower().split())


class BaseFetcher(ABC):
    @abstractmethod
    def fetch_recent(self, days_back: int = 1) -> list[Paper]:
        ...
