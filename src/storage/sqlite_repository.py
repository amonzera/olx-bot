from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from src.core.models import Alert, AlertConfig, AnalysisResult, Listing


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

                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    search_term TEXT NOT NULL,
                    location TEXT NOT NULL,
                    min_price_cents INTEGER,
                    max_price_cents INTEGER,
                    max_age_days INTEGER NOT NULL DEFAULT 30,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_scan_at TEXT
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

    def create_alert(
        self,
        *,
        chat_id: str,
        search_term: str,
        location: str,
        min_price_cents: int | None,
        max_price_cents: int | None,
        max_age_days: int,
    ) -> Alert:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO alerts (
                    chat_id, search_term, location, min_price_cents, max_price_cents, max_age_days
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    chat_id,
                    search_term.strip(),
                    location,
                    min_price_cents,
                    max_price_cents,
                    max_age_days,
                ),
            )
            row = conn.execute("SELECT * FROM alerts WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return self._alert_from_row(row)

    def get_alert(self, alert_id: int, chat_id: str | None = None) -> Alert | None:
        query = "SELECT * FROM alerts WHERE id = ?"
        params: tuple[object, ...]
        if chat_id is None:
            params = (alert_id,)
        else:
            query += " AND chat_id = ?"
            params = (alert_id, chat_id)

        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        return self._alert_from_row(row) if row else None

    def list_alerts(self, chat_id: str | None = None, *, active_only: bool = False) -> list[Alert]:
        where: list[str] = []
        params: list[object] = []
        if chat_id is not None:
            where.append("chat_id = ?")
            params.append(chat_id)
        if active_only:
            where.append("active = 1")

        query = "SELECT * FROM alerts"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY id ASC"

        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [self._alert_from_row(row) for row in rows]

    def list_active_alerts(self) -> list[Alert]:
        return self.list_alerts(active_only=True)

    def update_alert(
        self,
        *,
        alert_id: int,
        chat_id: str,
        search_term: str,
        location: str,
        min_price_cents: int | None,
        max_price_cents: int | None,
        max_age_days: int,
    ) -> Alert | None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE alerts
                SET search_term = ?,
                    location = ?,
                    min_price_cents = ?,
                    max_price_cents = ?,
                    max_age_days = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND chat_id = ?
                """,
                (
                    search_term.strip(),
                    location,
                    min_price_cents,
                    max_price_cents,
                    max_age_days,
                    alert_id,
                    chat_id,
                ),
            )
            row = conn.execute(
                "SELECT * FROM alerts WHERE id = ? AND chat_id = ?",
                (alert_id, chat_id),
            ).fetchone()
        return self._alert_from_row(row) if row else None

    def set_alert_active(self, *, alert_id: int, chat_id: str, active: bool) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE alerts
                SET active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND chat_id = ?
                """,
                (1 if active else 0, alert_id, chat_id),
            )
        return cursor.rowcount > 0

    def delete_alert(self, *, alert_id: int, chat_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM alerts WHERE id = ? AND chat_id = ?",
                (alert_id, chat_id),
            )
        return cursor.rowcount > 0

    def mark_alert_scanned(self, alert_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE alerts
                SET last_scan_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (alert_id,),
            )

    def _alert_key(self, alert: AlertConfig) -> str:
        if alert.alert_id is not None:
            return f"alert:{alert.alert_id}"
        return "|".join(
            [
                alert.search_term.strip().lower(),
                str(alert.min_price_cents or ""),
                str(alert.max_price_cents or ""),
                str(alert.min_expected_price_cents or ""),
                str(alert.target_price_cents or ""),
                str(alert.max_age_days),
                alert.location or "",
            ]
        )

    def _alert_from_row(self, row: sqlite3.Row) -> Alert:
        return Alert(
            id=int(row["id"]),
            chat_id=str(row["chat_id"]),
            search_term=str(row["search_term"]),
            location=str(row["location"]),
            min_price_cents=row["min_price_cents"],
            max_price_cents=row["max_price_cents"],
            max_age_days=int(row["max_age_days"]),
            active=bool(row["active"]),
            created_at=self._parse_datetime(row["created_at"]),
            updated_at=self._parse_datetime(row["updated_at"]),
            last_scan_at=self._parse_datetime(row["last_scan_at"]),
        )

    def _parse_datetime(self, value: object) -> datetime | None:
        if value is None:
            return None
        return datetime.fromisoformat(str(value))
