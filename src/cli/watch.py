from __future__ import annotations

import argparse
import logging
import time

from src.core.config import settings
from src.core.models import AlertConfig
from src.core.prices import parse_price_to_cents
from src.notifiers.factory import build_notifier
from src.scraper.client import OLXClient
from src.services.analyzer import OpportunityAnalyzer
from src.services.monitor import LocalMonitor
from src.storage.sqlite_repository import SQLiteRepository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Watch OLX locally with repeated HTTP scans.")
    parser.add_argument("term", help="Search term, for example: 'iphone 13'")
    parser.add_argument("--max-price", help="Maximum price, for example: 2500")
    parser.add_argument("--min-expected-price", help="Minimum believable price, for example: 1500")
    parser.add_argument("--target-price", help="Target opportunity price, defaults to --max-price")
    parser.add_argument("--max-age-days", type=int, default=settings.MAX_LISTING_AGE_DAYS)
    parser.add_argument("--interval", type=int, default=settings.DELAY_BETWEEN_REQUESTS_SECONDS)
    parser.add_argument("--db", default=settings.SQLITE_PATH)
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = build_parser().parse_args()

    alert = AlertConfig(
        search_term=args.term,
        max_price_cents=parse_price_to_cents(args.max_price),
        min_expected_price_cents=parse_price_to_cents(args.min_expected_price),
        target_price_cents=parse_price_to_cents(args.target_price) or parse_price_to_cents(args.max_price),
        max_age_days=args.max_age_days,
    )

    client = OLXClient()
    monitor = LocalMonitor(
        client=client,
        analyzer=OpportunityAnalyzer(),
        repository=SQLiteRepository(args.db),
        notifier=build_notifier(),
    )

    try:
        while True:
            result = monitor.scan_once(alert)
            logging.info(
                "Scan completed: fetched=%s analyzed=%s notified=%s",
                result.fetched_count,
                result.analyzed_count,
                result.notified_count,
            )
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logging.info("Stopped by user")
    finally:
        client.close()


if __name__ == "__main__":
    main()
