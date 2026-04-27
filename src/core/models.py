from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any


class SearchLocation(StrEnum):
    BRASIL = "brasil"
    RIO_DE_JANEIRO = "rio de janeiro"


class AnalysisFlag(StrEnum):
    LOW_PRICE_CAUTION = "LOW_PRICE_CAUTION"
    DEFECT_KEYWORD = "DEFECT_KEYWORD"
    SCAM_CAUTION = "SCAM_CAUTION"
    UNKNOWN_DATE = "UNKNOWN_DATE"
    RECENT = "RECENT"
    GOOD_PRICE = "GOOD_PRICE"


@dataclass(slots=True)
class AlertConfig:
    search_term: str
    min_price_cents: int | None = None
    max_price_cents: int | None = None
    min_expected_price_cents: int | None = None
    target_price_cents: int | None = None
    max_age_days: int = 30
    location: str = SearchLocation.BRASIL.value
    alert_id: int | None = None
    chat_id: str | None = None


@dataclass(slots=True)
class Alert:
    id: int
    chat_id: str
    search_term: str
    location: str
    min_price_cents: int | None
    max_price_cents: int | None
    max_age_days: int
    active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_scan_at: datetime | None = None

    def to_config(self) -> AlertConfig:
        return AlertConfig(
            search_term=self.search_term,
            min_price_cents=self.min_price_cents,
            max_price_cents=self.max_price_cents,
            target_price_cents=self.max_price_cents,
            max_age_days=self.max_age_days,
            location=self.location,
            alert_id=self.id,
            chat_id=self.chat_id,
        )


@dataclass(slots=True)
class Listing:
    external_id: str
    title: str
    price_cents: int | None
    url: str
    published_at: date | None = None
    raw_date: str | None = None
    location: str | None = None
    source: str = "olx"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AnalysisResult:
    listing_id: str
    score: int
    flags: list[AnalysisFlag]
    reasons: list[str]
    should_notify: bool
