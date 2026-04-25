from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any


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
    max_price_cents: int | None = None
    min_expected_price_cents: int | None = None
    target_price_cents: int | None = None
    max_age_days: int = 30
    location: str | None = None


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
