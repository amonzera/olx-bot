from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path

from src.core.models import AlertConfig, AnalysisResult, Listing


class SQLiteRepository:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    price_cents INTEGER,
                    url TEXT NOT NULL,
                    published_at TEXT,
                    raw_date TEXT,
                    location TEXT,
                    first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source, external_id)
                );

                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_key TEXT NOT NULL,
                    source TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    flags TEXT NOT NULL,
                    reasons TEXT NOT NULL,
                    notified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(alert_key, source, external_id)
                );
                """
            )

    def save_listing(self, listing: Listing) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO listings (
                    source, external_id, title, price_cents, url, published_at, raw_date, location
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    listing.source,
                    listing.external_id,
                    listing.title,
                    listing.price_cents,
                    listing.url,
                    listing.published_at.isoformat() if listing.published_at else None,
                    listing.raw_date,
                    listing.location,
                ),
            )

    def save_listings(self, listings: Iterable[Listing]) -> None:
        for listing in listings:
            self.save_listing(listing)

    def was_notified(self, alert: AlertConfig, listing: Listing) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT 1 FROM notifications
                WHERE alert_key = ? AND source = ? AND external_id = ?
                LIMIT 1
                """,
                (self._alert_key(alert), listing.source, listing.external_id),
            ).fetchone()
        return row is not None

    def mark_notified(self, alert: AlertConfig, listing: Listing, analysis: AnalysisResult) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO notifications (
                    alert_key, source, external_id, score, flags, reasons
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    self._alert_key(alert),
                    listing.source,
                    listing.external_id,
                    analysis.score,
                    ",".join(flag.value for flag in analysis.flags),
                    " | ".join(analysis.reasons),
                ),
            )

    def _alert_key(self, alert: AlertConfig) -> str:
        return "|".join(
            [
                alert.search_term.strip().lower(),
                str(alert.max_price_cents or ""),
                str(alert.min_expected_price_cents or ""),
                str(alert.target_price_cents or ""),
                str(alert.max_age_days),
                alert.location or "",
            ]
        )
