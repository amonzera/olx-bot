from __future__ import annotations

import re
import unicodedata
from datetime import UTC, date, datetime, timedelta


MONTHS = {
    "jan": 1,
    "janeiro": 1,
    "fev": 2,
    "fevereiro": 2,
    "mar": 3,
    "marco": 3,
    "março": 3,
    "abr": 4,
    "abril": 4,
    "mai": 5,
    "maio": 5,
    "jun": 6,
    "junho": 6,
    "jul": 7,
    "julho": 7,
    "ago": 8,
    "agosto": 8,
    "set": 9,
    "setembro": 9,
    "out": 10,
    "outubro": 10,
    "nov": 11,
    "novembro": 11,
    "dez": 12,
    "dezembro": 12,
}


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def parse_publication_date(value: object, today: date | None = None) -> date | None:
    """Parse common OLX absolute and relative publication dates."""
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    today = today or date.today()
    raw = str(value).strip()
    if not raw:
        return None

    text = normalize_text(raw)
    text = re.sub(r"\s+", " ", text)

    timestamp_date = _parse_unix_timestamp(text)
    if timestamp_date is not None:
        return timestamp_date

    if text in {"hoje", "publicado hoje"}:
        return today
    if text in {"ontem", "publicado ontem"}:
        return today - timedelta(days=1)

    iso_match = re.match(r"(\d{4})-(\d{2})-(\d{2})", text)
    if iso_match:
        return date.fromisoformat(iso_match.group(0))

    br_match = re.match(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", text)
    if br_match:
        day, month, year = [int(part) for part in br_match.groups()]
        if year < 100:
            year += 2000
        return date(year, month, day)

    relative_match = re.search(r"(?:ha|há)\s+(\d+|um|uma)\s+(dia|dias|semana|semanas|mes|meses)", text)
    if relative_match:
        amount_text, unit = relative_match.groups()
        amount = 1 if amount_text in {"um", "uma"} else int(amount_text)
        if unit.startswith("dia"):
            return today - timedelta(days=amount)
        if unit.startswith("semana"):
            return today - timedelta(days=amount * 7)
        return today - timedelta(days=amount * 30)

    day_month_match = re.search(r"(\d{1,2})\s+(?:de\s+)?([a-zç]{3,9})", text)
    if day_month_match:
        day = int(day_month_match.group(1))
        month_text = day_month_match.group(2)
        month = MONTHS.get(month_text)
        if month is None:
            return None
        year = today.year
        parsed = date(year, month, day)
        if parsed > today:
            parsed = date(year - 1, month, day)
        return parsed

    return None


def _parse_unix_timestamp(value: str) -> date | None:
    if not re.fullmatch(r"\d{10,13}", value):
        return None

    timestamp = int(value)
    if len(value) == 13:
        timestamp = timestamp // 1000

    try:
        return datetime.fromtimestamp(timestamp, tz=UTC).date()
    except (OSError, OverflowError, ValueError):
        return None


def is_recent(published_at: date | None, max_age_days: int, today: date | None = None) -> bool:
    if published_at is None:
        return False
    today = today or date.today()
    age = (today - published_at).days
    return 0 <= age <= max_age_days
