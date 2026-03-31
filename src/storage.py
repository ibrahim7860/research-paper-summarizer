from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path


class PaperStorage:
    def __init__(self, db_path: str):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self) -> None:
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id TEXT,
                normalized_title TEXT,
                title TEXT,
                source TEXT,
                summary TEXT,
                relevance_score REAL,
                key_takeaway TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(normalized_title)
            )
        """)
        self.conn.commit()

    def is_seen(self, normalized_title: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM papers WHERE normalized_title = ?", (normalized_title,)
        ).fetchone()
        return row is not None

    def mark_seen(
        self,
        external_id: str,
        normalized_title: str,
        title: str,
        source: str,
        summary: str = "",
        relevance_score: float = 0.0,
        key_takeaway: str = "",
    ) -> None:
        self.conn.execute(
            """INSERT OR IGNORE INTO papers
               (external_id, normalized_title, title, source, summary, relevance_score, key_takeaway, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (external_id, normalized_title, title, source, summary, relevance_score, key_takeaway, datetime.utcnow()),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
