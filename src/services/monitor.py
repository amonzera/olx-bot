from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from src.core.models import AlertConfig, AnalysisResult, Listing
from src.scraper.client import OLXClient
from src.scraper.parsers import parse_search_results
from src.services.analyzer import OpportunityAnalyzer
from src.storage.sqlite_repository import SQLiteRepository

logger = logging.getLogger(__name__)


class Notifier(Protocol):
    def send(self, listing: Listing, analysis: AnalysisResult) -> None:
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
        html = self.client.fetch_search_page(
            search_term=alert.search_term,
            max_price=(alert.max_price_cents // 100 if alert.max_price_cents else None),
        )
        if not html:
            logger.warning("No HTML returned for alert %s", alert.search_term)
            return MonitorResult(0, 0, 0, [], [])

        listings = parse_search_results(html)
        analyses: list[AnalysisResult] = []
        notified_count = 0

        for listing in listings:
            self.repository.save_listing(listing)
            analysis = self.analyzer.analyze(listing, alert)
            analyses.append(analysis)

            if not analysis.should_notify:
                continue
            if self.repository.was_notified(alert, listing):
                continue

            self.notifier.send(listing, analysis)
            self.repository.mark_notified(alert, listing, analysis)
            notified_count += 1

        return MonitorResult(
            fetched_count=len(listings),
            analyzed_count=len(analyses),
            notified_count=notified_count,
            listings=listings,
            analyses=analyses,
        )
