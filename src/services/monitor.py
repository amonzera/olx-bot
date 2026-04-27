from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Protocol

from src.core.config import settings
from src.core.dates import is_recent
from src.core.models import AlertConfig, AnalysisResult, Listing
from src.scraper.client import OLXClient
from src.scraper.parsers import parse_search_results
from src.services.analyzer import OpportunityAnalyzer
from src.storage.sqlite_repository import SQLiteRepository

logger = logging.getLogger(__name__)


class Notifier(Protocol):
    def send(self, alert: AlertConfig, listing: Listing, analysis: AnalysisResult) -> None:
        ...


@dataclass(slots=True)
class MonitorResult:
    fetched_count: int
    analyzed_count: int
    notified_count: int
    listings: list[Listing]
    analyses: list[AnalysisResult]


class LocalMonitor:
    def __init__(
        self,
        client: OLXClient,
        analyzer: OpportunityAnalyzer,
        repository: SQLiteRepository,
        notifier: Notifier,
    ):
        self.client = client
        self.analyzer = analyzer
        self.repository = repository
        self.notifier = notifier

    def scan_once(self, alert: AlertConfig) -> MonitorResult:
        listings: list[Listing] = []
        analyses: list[AnalysisResult] = []
        notified_count = 0
        seen: set[tuple[str, str]] = set()

        for page in range(1, settings.MAX_SEARCH_PAGES + 1):
            if page > 1:
                time.sleep(settings.DELAY_BETWEEN_PAGE_REQUESTS_SECONDS)

            html = self.client.fetch_search_page(
                search_term=alert.search_term,
                location=alert.location,
                min_price=(alert.min_price_cents // 100 if alert.min_price_cents else None),
                max_price=(alert.max_price_cents // 100 if alert.max_price_cents else None),
                page=page,
            )
            if not html:
                if page == 1:
                    logger.warning("No HTML returned for alert %s", alert.search_term)
                break

            page_listings = parse_search_results(html)
            if not page_listings:
                break

            for listing in page_listings:
                key = (listing.source, listing.external_id)
                if key in seen:
                    continue
                seen.add(key)
                listings.append(listing)

                self.repository.save_listing(listing)
                analysis = self.analyzer.analyze(listing, alert)
                analyses.append(analysis)

                if not analysis.should_notify:
                    continue
                if self.repository.was_notified(alert, listing):
                    continue

                self.notifier.send(alert, listing, analysis)
                self.repository.mark_notified(alert, listing, analysis)
                notified_count += 1

            if self._page_is_outside_recent_window(page_listings, alert):
                break

        return MonitorResult(
            fetched_count=len(listings),
            analyzed_count=len(analyses),
            notified_count=notified_count,
            listings=listings,
            analyses=analyses,
        )

    def _page_is_outside_recent_window(self, listings: list[Listing], alert: AlertConfig) -> bool:
        known_dates = [listing.published_at for listing in listings if listing.published_at is not None]
        if not known_dates:
            return False
        return all(not is_recent(published_at, alert.max_age_days) for published_at in known_dates)
